# Built in imports.
import json
import asyncio
import io
import time
# Third Party imports.
import openpyxl as opxl
import pandas as pd
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer
# Scripts.
from .upload import *
from .models import *

#temp while obtaining the user
from django.contrib.auth.models import User


class RegistryConsumer(AsyncWebsocketConsumer): 
    def __init__(self, scope, **kwargs):
        super(RegistryConsumer, self).__init__(scope, **kwargs)
        self.columns = [x+str(y) for x in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'] for y in range(1,13)]
        self.file_binary = b''
        self.meta_dict = {}
        self.assay_id = 0
        self.machine = ''
        self.signal_names = []

    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add(
            "upload",
            self.channel_name
        )

    # TO DO: setup message receiving and disconnection
    async def initialize_upload(self, data):
        print(f"initialize_upload DATA: {data}", flush=True)
        self.machine = data['machine']
        
        print(f"self.machine: {self.machine}", flush=True)
        # Do stuff with the data (study id, assay data, etc...)

        print(f"data['study']: {data['study']}", flush=True)

        assay = Assay(study=Study.objects.get(id=data['study']), 
                    name=data['name'], 
                    machine=self.machine, 
                    description=data['description'], 
                    temperature=float(data['temperature']))
        assay.save()
        print(f"assay.id FROM OBJECT: {assay.id}")
        self.assay_id = assay.id

        # Send message for receiving file
        await self.send(text_data=json.dumps({
                'type': 'ready_for_file',
                'data': {'assay_id': self.assay_id}
            }))


    async def read_binary(self, bin_data):
        self.file_binary = bin_data

        # Do stuff with the excel
        wb = opxl.load_workbook(filename=io.BytesIO(bin_data), data_only=True)
        ws = wb['Data']
        self.signal_names = synergy_get_signal_names(ws)
        
        print(f"self.signal_names READ BINARY: {self.signal_names}", flush=True)
        
        ###########################
        ## REVIEW this method ##
        # get dnas and inducers
        self.meta_dict = synergy_load_meta(wb, self.columns)

        dna_keys = [val for val in self.meta_dict.index if "DNA" in val]
        inds = [val for val in self.meta_dict.index if "conc" in val]
        dnas = [np.unique(self.meta_dict.loc[k]) for k in dna_keys]
        all_dnas = []
        for dna in dnas:
            all_dnas += list(dna)

        ###########################
        
        # Ask for dna, inducers and signals
        await self.send(text_data=json.dumps({
                'type': 'input_requests',
                'data': {
                    'dna': all_dnas,
                    'inducer': inds,
                    'signal': self.signal_names[:-1]
                }
            }))


    async def parse_metadata(self, metadata):
        print(f"metadata: {metadata}", flush=True)
        # Do stuff with the excel
        wb = opxl.load_workbook(filename=io.BytesIO(self.file_binary), data_only=True)
        ws = wb['Data']
        
        # get dnas and inducers
        signal_map = {}

        print(f"metadata.keys(): {metadata.keys()}", flush=True)

        for i, s_id in enumerate(metadata['signal']):
            signal_map[self.signal_names[i]] = Signal.objects.get(id=s_id).name

        print(f"signal_map: {signal_map}", flush=True)

        dfs = synergy_load_data(ws, self.signal_names, signal_map)
        
        print(f"self.assay_id: {self.assay_id}", flush=True)
        start = time.time()
        await self.upload_data(self.assay_id, self.meta_dict, dfs, {})
        end = time.time()
        print(f"FINISHED UPLOADING. Took {end-start} secs")
        await self.send(text_data=json.dumps({
                'type': 'creation_done'
            }))


    async def progress_update(self, progress):
        print(f"progress: {progress}", flush=True)
        await self.send(text_data=json.dumps({
                'type': 'progress',
                'data': progress
            }))


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

    async def upload_data(self, assay_id, meta_dict, dfs, dna_map):
        print(f"assay_id in upload_data: {assay_id}")
        columns = list(meta_dict.columns)
        meta_dnas = [k for k in list(meta_dict.index) if 'DNA' in k]
        meta_inds = [k for k in list(meta_dict.index) if 'conc' in k]
        for well_idx, well in enumerate(columns):
            existing_dna = [i.names for i in Dna.objects.all()]
            existing_med = [i.name for i in Media.objects.all()]
            existing_str = [i.name for i in Strain.objects.all()]
            existing_ind = [(i.names, i.concentrations) for i in Inducer.objects.all()]

            # Metadata value for each well (sample): strain and media
            s_media = meta_dict.loc['Media'][well]
            s_strain = meta_dict.loc['Strains'][well]

            if s_media.upper() != 'NONE':
                if s_media not in existing_med:
                    media = Media(name=s_media, description='')
                    media.save()
                else:
                    media = Media.objects.filter(name__exact=s_media)[0]

                if s_strain not in existing_str:
                    strain = Strain(name=s_strain, description='')
                    strain.save()
                else:
                    strain = Strain.objects.filter(name__exact=s_strain)[0]

                dnas = []
                for meta_dna in meta_dnas:
                    s_dna = meta_dict.loc[meta_dna][well]
                    dnas.append(s_dna)
                # Get unique DNA names
                dnas = list(set(dnas))
                # If we have a real DNA, remove the 'None's
                if len(dnas)>1 and 'None' in dnas:
                    dnas.remove('None')

                dnas.sort()

                # When dna_map = {} (all dnas already in DB), no dna_map[dna] to get
                # BUg: When dnas = ['None] error
                try:
                    sboluris = [dna_map[dna] for dna in dnas]
                except:
                    sboluris = []

                if dnas not in existing_dna:
                    d = Dna(names=dnas, sboluris=sboluris)
                    d.save()
                else:
                    d = Dna.objects.filter(names__exact=dnas)[0]


                if len(meta_inds) > 0:
                    inds = [ind.split(' ')[0] for ind in meta_inds]
                    concs = [meta_dict.loc[meta_ind][well] for meta_ind in meta_inds]
                    concs = list(map(float, concs))
                    # Removes not present inducers
                    ind_non_zero = np.where(np.array(concs) != 0.)
                    inds = list(np.array(inds)[ind_non_zero])
                    concs = [float(c) for c in list(np.array(concs)[ind_non_zero])]

                    if (inds, concs) not in existing_ind:
                        i = Inducer(names=inds, concentrations=concs)
                        i.save()
                    else:
                        i = Inducer.objects.filter(names__exact=inds).filter(concentrations__exact=concs)[0]
                else:
                    if ([], []) not in existing_ind:
                        i = Inducer(names=[], concentrations=[])
                        i.save()
                    else:
                        i = Inducer.objects.filter(names__exact=[]).filter(concentrations__exact=[])[0]

                s = Sample(assay=Assay.objects.get(id=assay_id), media=media, strain=strain, dna=d, inducer=i, row=well[0], col=well[1:])
                s.save()


                # status update
                #process_percent = (96*file_idx+(well_idx+1))/(96*files_number)
                
                #progress_update(process_percent)
                print("progress being called", flush=True)
                await self.progress_update(10)

                # Data value for each well
                measurements = []
                for key, dfm in dfs.items():
                    signal = Signal.objects.get(name=key)
                    for i, value in enumerate(dfm[well]):
                        #m_name = key
                        m_value = value
                        m_time = dfm['Time'].iloc[i]
                        m = Measurement(sample=s, signal=signal, value=m_value, time=m_time)
                        measurements.append(m)
                Measurement.objects.bulk_create(measurements)

            else:
                print("I'm None")