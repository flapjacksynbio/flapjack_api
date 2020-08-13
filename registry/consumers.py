# Built in imports.
import json
import asyncio
import io
import time
from django.db.models import Q
# Third Party imports.
import openpyxl as opxl
import numpy as np
import pandas as pd
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer
# Scripts.
from .upload import *
from .models import *
from .util import *

empty_dna_names = ['none', 'None', '']

class MeasurementsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add(
            "measurements",
            self.channel_name
        )
        
    async def receive(self, text_data):
        print(f"Receive. text_data: {text_data}", flush=True)
        data = json.loads(text_data)
        if data['type'] == 'measurements':
            params = data['parameters']
            signals = params.get('signal')
            analysis_params = params.get('analysis')
            s = get_samples(params)
            df = get_measurements(s, signals)
            await self.send(text_data=json.dumps({
                'type': 'measurements',
                'data': df.to_json()
            }))

    async def disconnect(self, message):
        await self.channel_layer.group_discard(
            "measurements",
            self.channel_name
        )
        
class UploadConsumer(AsyncWebsocketConsumer): 
    def __init__(self, scope, **kwargs):
        super(UploadConsumer, self).__init__(scope, **kwargs)
        # for most attrs is not necessary to declared them, it is  
        # for having an idea of which parameters the instance has
        self.columns = [x+str(y) for x in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'] for y in range(1,13)]
        self.meta_dict = {}
        self.assay_id = 0
        self.machine = ''
        self.signal_names = []
        self.ws = ''
        self.dna_names = []
        self.binary_file = b''

    async def connect(self):
        self.user = User.objects.get(username=self.scope["user"])
        await self.accept()
        await self.channel_layer.group_add(
            "upload",
            self.channel_name
        )

    # TO DO: setup message receiving and disconnection
    async def initialize_upload(self, data):
        print(f"initialize_upload DATA: {data}", flush=True)
        self.machine = data['machine']
        
        # create assay object and store id as attribute
        assay = Assay(study=Study.objects.get(id=data['study']), 
                    name=data['name'], 
                    machine=self.machine, 
                    description=data['description'], 
                    temperature=float(data['temperature']))
        assay.save()
        self.assay_id = assay.id

        # Send message for receiving file
        await self.send(text_data=json.dumps({
                'type': 'ready_for_file',
                'data': {'assay_id': self.assay_id}
            }))


    async def read_binary(self, bin_data):
        ## IF MACHINE SYNERGY
        if 'synergy' in self.machine.lower():
            # load workbook, sheet containing data and extract metadata information
            wb = opxl.load_workbook(filename=io.BytesIO(bin_data), data_only=True)
            self.ws = wb['Data']
            self.signal_names = synergy_get_signal_names(self.ws)[:-1]
            self.meta_dict = synergy_load_meta(wb, self.columns)
            
            # get dnas and chemicals names to ask for metadata to the user
            dna_keys = [val for val in self.meta_dict.index if "DNA" in val]
            dna_lists = [list(np.unique(self.meta_dict.loc[k])) for k in dna_keys]
            self.dna_names = list(
                np.unique(
                    [dna for dna_list in dna_lists for dna in dna_list if dna not in empty_dna_names]
                    )
                )
            chem_names_file = [val for val in self.meta_dict.index if "chem" in val]


        ## IF MACHINE FLUOPI
        elif 'fluopi' in self.machine.lower():
            self.binary_file = bin_data
            data = json.loads(self.binary_file.decode())
            
            # dnas
            col_dnas = data['dnas']
            self.dna_names = list(np.unique(list(col_dnas.values())))
            # as for now, no chemicals are included
            chem_names_file = []
            # fluo per channel per colony
            fluo = data['Fluorescence Intensity']
            self.signal_names = list(fluo.keys())

        ## IF MACHINE BMG


        ## SEND CORRECT DATA DEPENDING ON THE FILE
        # Ask for dna, chemicals and signals
        await self.send(text_data=json.dumps({
                'type': 'input_requests',
                'data': {
                    'dna': self.dna_names,
                    'chemical': chem_names_file,
                    'signal': self.signal_names
                }
            }))


    async def parse_metadata(self, metadata):
        print(f"metadata: {metadata}", flush=True)
        ## IF MACHINE SYNERGY
        if 'synergy' in self.machine.lower():
            # get dnas and inducers
            # construct signal_map ({signal_name: signal from machine})
            signal_map = {self.signal_names[i]:Signal.objects.get(id=s_id).name 
                            for i, s_id in enumerate(metadata['signal'])} 

            # load data from "Data" sheet as a DataFrame
            signal_names_aux = self.signal_names.copy()
            signal_names_aux.append('Results')
            dfs = synergy_load_data(self.ws, signal_names_aux, signal_map)
            
            signal_ids = {signal_map[name]: metadata['signal'][idx] 
                            for idx, name in enumerate(self.signal_names)}
            # upload data
            start = time.time()
            await self.upload_data(self.assay_id, self.meta_dict, dfs, metadata, signal_ids)
            end = time.time()
            print(f"UPLOAD SYNERGY FINISHED. Took {end-start} secs")


        ## IF MACHINE FLUOPI
        elif 'fluopi' in self.machine.lower():
            data = json.loads(self.binary_file.decode())

            # time domain for the experiment
            time_serie = data['Times']
            # dnas
            col_dnas = data['dnas']
            # selected colonies when creating .json file with FluoPi's package
            sel_cols = data['Selected colonies']
            # used for?
            cols_in_assay = len(sel_cols)
            col_per_assay = len(sel_cols)
            # radius in time for each colony
            rad = data['Radius']
            # colony positions
            pos = data['pos']
            # fluo
            fluo = data['Fluorescence Intensity']
            # media
            media = data['media']
            # strain
            strain = data['strain']

            dna_map = {self.dna_names[idx]: dna_id for idx, dna_id in enumerate(metadata['dna'])}
            signal_map = {self.signal_names[idx]: signal_id for idx, signal_id in enumerate(metadata['signal'])}

            start = time.time()
            await self.fluopi_upload(self.assay_id, 
                        time_serie, 
                        sel_cols,
                        rad,
                        pos,
                        fluo,
                        self.dna_names,
                        media[0],
                        strain[0],
                        col_dnas,
                        dna_map,
                        signal_map)       
            
            end = time.time()
            print(f"UPLOAD FLUOPI FINISHED. Took {end-start} secs")
        ## IF MACHINE BMG
        
        await self.send(text_data=json.dumps({
                'type': 'creation_done'
            }))

    async def progress_update(self, progress):
        print(f"progress: {progress}", flush=True)
        await self.send(text_data=json.dumps({
                'type': 'progress',
                'data': progress
            }))
        await asyncio.sleep(0)

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            print("text_data", flush=True)
            data = json.loads(text_data)
            if data['type'] == 'init_upload':
                print("init_upload", flush=True)
                await self.initialize_upload(data['data'])
            elif data['type'] == 'metadata':
                print("metadata", flush=True)
                await self.parse_metadata(data['data'])

        if bytes_data:
            print('received bytes data:', len(bytes_data), flush=True)
            await self.read_binary(bytes_data)
        

    async def websocket_disconnect(self, message):
        await self.channel_layer.group_discard(
            "upload",
            self.channel_name
        )

    # TO DO: move part of this function to upload.py utils
    async def upload_data(self, assay_id, meta_dict, dfs, metadata, signal_ids):
        columns = list(meta_dict.columns)
        meta_dnas = [k for k in list(meta_dict.index) if 'DNA' in k]
        meta_inds = [k for k in list(meta_dict.index) if 'chem' in k]
        for well_idx, well in enumerate(columns):
            existing_med = [i.name for i in Media.objects.all()]
            existing_str = [i.name for i in Strain.objects.all()]
            existing_vec = [vec for vec in Vector.objects.all()]
            existing_sup = [(s.chemical.id, s.concentration) for s in Supplement.objects.all()]

            # Metadata value for each well (sample): strain and media
            s_media = meta_dict.loc['Media'][well]
            s_strain = meta_dict.loc['Strains'][well]

            # skip well if media==None
            if s_media.upper() != 'NONE':
                # create Media object
                if s_media not in existing_med:
                    media = Media(name=s_media, description='')
                    media.save()
                else:
                    media = Media.objects.filter(name__exact=s_media)[0]
                
                # create Strain object
                if s_strain.upper()=='NONE':
                    strain = None
                else:
                    if s_strain not in existing_str:
                        strain = Strain(name=s_strain, description='')
                        strain.save()
                    else:
                        strain = Strain.objects.filter(name__exact=s_strain)[0]

                # create Vector object
                vec_aux = Vector.objects.create()
                #for dna_id in metadata['dna']:
                no_dnas = True
                for dna in meta_dict.loc[meta_dnas][well]:
                    if dna in self.dna_names:
                        idx = np.where(np.array(self.dna_names)==dna)[0][0]
                        vec_aux.dnas.add(Dna.objects.get(id=metadata['dna'][idx]))
                        no_dnas = False
                if no_dnas:
                    # No vector to add
                    vector = None
                    vec_aux.delete()
                else:                    
                    # TO DO: find a better way of doing this
                    # checks if vector already exists in database
                    vec_exists = 0
                    for v in existing_vec:
                        if set(vec_aux.dnas.all())==set(v.dnas.all()):
                            vec_exists = 1
                            vector = v
                            vec_aux.delete()
                            break
                    if not vec_exists:
                        # add names
                        names = [dna.name for dna in vec_aux.dnas.all()]
                        names.sort()
                        vec_aux.name = '+'.join(names)
                        vec_aux.save()
                        vector = vec_aux

                # create chemicals and supplements
                # checking either len(metadata['chemical']) or len(meta_inds) > 0
                sample_supps = []
                if len(meta_inds) > 0:
                    concs = [float(meta_dict.loc[meta_ind][well]) for meta_ind in meta_inds]
                    for i, chem_id in enumerate(metadata['chemical']):
                        chemical = Chemical.objects.get(id=chem_id)
                        if concs[i] > 0.:
                            if (chemical.id, concs[i]) not in existing_sup:
                                # make func
                                conc_log = np.log10(concs[i])
                                if conc_log >= 0:
                                    units = 'M'
                                    cons_str= str(concs[i])
                                elif (conc_log < 0) and (conc_log) > -3:
                                    if concs[i]*1e3 < 100:
                                        cons_str= f"{concs[i]*1e3:.2f}"
                                        units = 'mM'
                                    else:
                                        cons_str= f"{concs[i]:.2f}"
                                        units = '\u03BCM'                      
                                elif (conc_log <= -3) and (conc_log) > -6:
                                    if concs[i]*1e6 < 100:
                                        units = '\u03BCM'
                                        cons_str= f"{concs[i]*1e6:.2f}"
                                    else:
                                        units = 'nM'
                                        cons_str= f"{concs[i]*1e3:.2f}"
                                elif (conc_log <= -6) and (conc_log) > -9:
                                    if concs[i]*1e9 < 100:
                                        units = 'nM'
                                        cons_str= f"{concs[i]*1e9:.2f}"
                                    else:
                                        units = 'pM'
                                        cons_str= f"{concs[i]*1e6:.2f}"
                                elif (conc_log <= -9) and (conc_log) > -12:
                                    units = 'pM'
                                    cons_str= f"{concs[i]*1e12:.2f}"
                                sup = Supplement(name=f"{chemical.name} = {cons_str} {units}", 
                                                chemical=chemical, 
                                                concentration=concs[i])
                                sup.save()
                            else:
                                sup = Supplement.objects.get(chemical=chemical, concentration=concs[i])
                            sample_supps.append(sup)

                # create Sample object
                samp = Sample(assay=Assay.objects.get(id=assay_id), 
                                media=media, 
                                strain=strain, 
                                vector=vector, 
                                row=well[0], 
                                col=well[1:])
                samp.save()
                # assign supplements to sample
                for sup in sample_supps:
                    samp.supplements.add(sup)

                # Data value for each well
                measurements = []
                for key, dfm in dfs.items():
                    # TO DO: decide whether to check for user's signals or public ones
                    signal = Signal.objects.filter(id=signal_ids[key])[0]
                    #signal = Signal.objects.filter(Q(measurement__sample__assay__study__owner=self.user) & 
                    #                               Q(name='OD')).distinct()[0]
                    for i, value in enumerate(dfm[well]):
                        m_value = value
                        m_time = dfm['Time'].iloc[i]
                        m = Measurement(sample=samp, signal=signal, value=m_value, time=m_time)
                        measurements.append(m)
                Measurement.objects.bulk_create(measurements)

                # status update
                process_percent = (well_idx+1)/(len(columns))
                await self.progress_update(process_percent)

            else:
                print("I'm Media None")

    async def fluopi_upload(self, 
                            assay_id, 
                            time_serie, 
                            sel_cols,
                            rad,
                            pos,
                            fluo,
                            dna_names,
                            media,
                            strain,
                            col_dnas,
                            dna_map,
                            signal_map):
        
        existing_med = [m.name for m in Media.objects.all()]
        existing_str = [s.name for s in Strain.objects.all()]

        # Media
        if media not in existing_med:
            media = Media(name=media, description='')
            media.save()
        else:
            media = Media.objects.filter(name__exact=media)[0]

        # Strain
        if strain not in existing_str:
            strain = Strain(name=strain, description='')
            strain.save()
        else:
            strain = Strain.objects.filter(name__exact=strain)[0]

        measurements = []
        for col_idx, col in enumerate(sel_cols):
            # Vector
            # construct a list of lists, each containing the ids of the dnas
            # in each vector, for the requesting user
            user_vectors = Vector.objects.filter(
                Q(sample__assay__study__owner=self.user) |
                Q(sample__assay__study__public=True) |
                Q(sample__assay__study__shared_with=self.user)
            ).distinct()
            
            vectors_dna_ids = []
            vector_ids = [v.id for v in user_vectors]
            for v in user_vectors:
                vector_dna_ids = [dna.id for dna in v.dnas.all()]
                vector_dna_ids.sort()
                vectors_dna_ids.append(vector_dna_ids)

            # dna in this colony (col_dnas[col])
            col_dna_ids = [dna_map[d] for d in col_dnas[str(col)]]
            col_dna_ids.sort()

            # if colony dnas already exist in a vector, we assign that object
            if col_dna_ids in vectors_dna_ids:
                idx = vectors_dna_ids.index(col_dna_ids)
                vector_id = vector_ids[idx]
                vector = Vector.objects.get(id=vector_id)
            else:
                vector = Vector.objects.create()
                for dna_id in col_dna_ids:
                    vector.dnas.add(Dna.objects.get(id=dna_id))
                vector.save()     

            # Sample 
            samp = Sample(assay=Assay.objects.get(id=assay_id), 
                                    media=media, 
                                    strain=strain, 
                                    vector=vector, 
                                    row=pos[str(col)][0], 
                                    col=pos[str(col)][1])
            samp.save()
            
            # area as OD
            # TO DO: Area Signal is created if not exists. Think on a better way
            try:
                od_signal = Signal.objects.get(name='Area')
            except:
                od_signal = Signal(name='Area', description='', color='')
                od_signal.save()
            
            for idx, r in enumerate(rad[str(col)]):
                mar = Measurement(sample=samp, signal=od_signal, value=(r**2)*np.pi, time=time_serie[idx])
                measurements.append(mar)
            
            # Fluo
            for f_name in fluo.keys():
                f_signal = Signal.objects.get(id=signal_map[f_name])
                for idx, val in enumerate(fluo[f_name][str(col)]):
                    m = Measurement(sample=samp, signal=f_signal, value=val, time=time_serie[idx])
                    measurements.append(m)

            # status update
            process_percent = (col_idx+1)/(len(sel_cols))
            await self.progress_update(process_percent)

        Measurement.objects.bulk_create(measurements)
        