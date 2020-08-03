# Built in imports.
import json
import asyncio
import io
import time
# Third Party imports.
import openpyxl as opxl
import pandas as pd
import numpy as np
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer
# Scripts.
from .upload import synergy_get_signal_names, synergy_load_meta, synergy_load_data
from .models import Assay, Chemical, Dna, Measurement, Media, Signal, Strain, Study, Supplement, Vector


class RegistryConsumer(AsyncWebsocketConsumer):
    def __init__(self, scope, **kwargs):
        super(RegistryConsumer, self).__init__(scope, **kwargs)
        # for most attrs is not necessary to declared them, it is
        # for having an idea of which parameters the instance has
        self.columns = [x+str(y) for x in ['A', 'B', 'C',
                                           'D', 'E', 'F', 'G', 'H'] for y in range(1, 13)]
        self.meta_dict = {}
        self.assay_id = 0
        self.machine = ''
        self.signal_names = []
        self.ws = ''
        self.dna_names = []

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
        # load workbook, sheet containing data and extract metadata information
        wb = opxl.load_workbook(filename=io.BytesIO(bin_data), data_only=True)
        self.ws = wb['Data']
        self.signal_names = synergy_get_signal_names(self.ws)
        self.meta_dict = synergy_load_meta(wb, self.columns)

        # get dnas and chemicals names to ask for metadata to the user
        dna_keys = [val for val in self.meta_dict.index if "DNA" in val]
        dna_lists = [list(np.unique(self.meta_dict.loc[k])) for k in dna_keys]
        self.dna_names = list(
            np.unique([dna for dna_list in dna_lists for dna in dna_list]))
        chem_names_excel = [
            val for val in self.meta_dict.index if "chem" in val]

        # Ask for dna, chemicals and signals
        await self.send(text_data=json.dumps({
            'type': 'input_requests',
            'data': {
                    'dna': self.dna_names,
                    'chemical': chem_names_excel,
                    'signal': self.signal_names[:-1]
            }
        }))

    async def parse_metadata(self, metadata):
        print(f"metadata: {metadata}", flush=True)
        # get dnas and inducers
        # construct signal_map ({signal_name: signal from machine})
        signal_map = {self.signal_names[i]: Signal.objects.get(id=s_id).name
                      for i, s_id in enumerate(metadata['signal'])}

        # load data from "Data" sheet as a DataFrame
        dfs = synergy_load_data(self.ws, self.signal_names, signal_map)

        # upload data
        start = time.time()
        await self.upload_data(self.assay_id, self.meta_dict, dfs, metadata)
        end = time.time()
        print(f"UPLOAD FINISHED. Took {end-start} secs")

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

    # TO DO: move part of this function to upload.py utils
    async def upload_data(self, assay_id, meta_dict, dfs, metadata):
        columns = list(meta_dict.columns)
        meta_dnas = [k for k in list(meta_dict.index) if 'DNA' in k]
        meta_inds = [k for k in list(meta_dict.index) if 'chem' in k]
        for well_idx, well in enumerate(columns):
            existing_med = [i.name for i in Media.objects.all()]
            existing_str = [i.name for i in Strain.objects.all()]
            existing_vec = [vec for vec in Vector.objects.all()]
            existing_sup = [(s.chemical.id, s.concentration)
                            for s in Supplement.objects.all()]

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
                if s_strain not in existing_str:
                    strain = Strain(name=s_strain, description='')
                    strain.save()
                else:
                    strain = Strain.objects.filter(name__exact=s_strain)[0]

                # create Vector object
                vec_aux = Vector.objects.create()
                # for dna_id in metadata['dna']:
                for dna in meta_dict.loc[meta_dnas][well]:
                    if dna in self.dna_names:
                        idx = np.where(np.array(self.dna_names) == dna)[0][0]
                        vec_aux.dnas.add(Dna.objects.get(
                            id=metadata['dna'][idx]))

                # TO DO: find a better way of doing this
                # checks if vector already exists in database
                vec_exists = 0
                for v in existing_vec:
                    if set(vec_aux.dnas.all()) == set(v.dnas.all()):
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
                    concs = [float(meta_dict.loc[meta_ind][well])
                             for meta_ind in meta_inds]
                    for i, chem_id in enumerate(metadata['chemical']):
                        chemical = Chemical.objects.get(id=chem_id)
                        if concs[i] > 0.:
                            if (chemical.id, concs[i]) not in existing_sup:
                                # make func
                                conc_log = np.log10(concs[i])
                                if conc_log >= 0:
                                    units = 'M'
                                    cons_str = str(concs[i])
                                elif (conc_log < 0) and (conc_log) > -3:
                                    if concs[i]*1e3 < 100:
                                        cons_str = f"{concs[i]*1e3:.2f}"
                                        units = 'mM'
                                    else:
                                        cons_str = f"{concs[i]:.2f}"
                                        units = '\u03BCM'
                                elif (conc_log <= -3) and (conc_log) > -6:
                                    if concs[i]*1e6 < 100:
                                        units = '\u03BCM'
                                        cons_str = f"{concs[i]*1e6:.2f}"
                                    else:
                                        units = 'nM'
                                        cons_str = f"{concs[i]*1e3:.2f}"
                                elif (conc_log <= -6) and (conc_log) > -9:
                                    if concs[i]*1e9 < 100:
                                        units = 'nM'
                                        cons_str = f"{concs[i]*1e9:.2f}"
                                    else:
                                        units = 'pM'
                                        cons_str = f"{concs[i]*1e6:.2f}"
                                elif (conc_log <= -9) and (conc_log) > -12:
                                    units = 'pM'
                                    cons_str = f"{concs[i]*1e12:.2f}"
                                sup = Supplement(name=f"{chemical.name} = {cons_str} {units}",
                                                 chemical=chemical,
                                                 concentration=concs[i])
                                sup.save()
                            else:
                                sup = Supplement.objects.get(
                                    chemical=chemical, concentration=concs[i])
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

                # status update
                process_percent = (well_idx+1)/(len(columns))
                await self.progress_update(process_percent)

                # Data value for each well
                measurements = []
                for key, dfm in dfs.items():
                    signal = Signal.objects.get(name=key)
                    for i, value in enumerate(dfm[well]):
                        m_value = value
                        m_time = dfm['Time'].iloc[i]
                        m = Measurement(sample=samp, signal=signal,
                                        value=m_value, time=m_time)
                        measurements.append(m)
                Measurement.objects.bulk_create(measurements)

            else:
                print("I'm Media None")
