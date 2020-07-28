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

# hardcoded, get from frontend
#columns = [x+str(y) for x in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'] for y in range(1,13)]
#file_binary = []
#meta_dict_mem = []
#assay_id = []
#machine = []

class RegistryConsumer(AsyncWebsocketConsumer): 
    #"""
    def __init__(self, scope, **kwargs):
        super(RegistryConsumer, self).__init__(scope, **kwargs)
        print("In init")

        self.test = "Hola soy new arg"
        self.columns = [x+str(y) for x in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'] for y in range(1,13)]
        self.file_binary = b''
        self.meta_dict = {}
        self.assay_id = 0
        self.machine = ''

        print(f"self.test: {self.test}", flush=True)
    #"""
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add(
            "upload",
            self.channel_name
        )

    # TO DO: setup message receiving and disconnection
    async def initialize_upload(self, data):

        #print(f"Test de atributos: {self.test}")

        print(data)
        #machine.append(data['machine'])
        self.machine = data['machine']
        
        print(f"self.machine: {self.machine}", flush=True)
        # Do stuff with the data (study id, assay data, etc...)

        # create assay, how to send id ???
        print(f"data['study']: {data['study']}", flush=True)

        assay = Assay(study=Study.objects.get(id=data['study']), 
                    name=data['name'], 
                    machine=self.machine, 
                    description=data['description'], 
                    temperature=float(data['temperature']))
        assay.save()
        print(f"assay.id: {assay.id}")
        #assay_id.append(assay.id)
        self.assay_id = assay.id

        # Send message for receiving file
        await self.send(text_data=json.dumps({
                'type': 'ready_for_file',
                'data': {'assay_id': self.assay_id}
            }))


    async def read_binary(self, bin_data):
        print(f"type(self.columns): {type(self.columns)}", flush=True)
        print(f"type(self.file_binary): {type(self.file_binary)}", flush=True)

        #file_binary.append(bin_data)
        self.file_binary = bin_data

        # Do stuff with the excel
        wb = opxl.load_workbook(filename=io.BytesIO(bin_data), data_only=True)
        ws = wb['Data']
        #assay_name = os.path.splitext(file_name)[0], 
        signal_names = synergy_get_signal_names(ws)
        
        #print(f"assay_name: {assay_name}", flush=True)
        print(f"signal_names: {signal_names}", flush=True)
        
        # get dnas and inducers
        self.meta_dict = synergy_load_meta(wb, self.columns)
        #meta_dict_mem.append(meta_dict)

        dna_keys = [val for val in self.meta_dict.index if "DNA" in val]
        inds = [val for val in self.meta_dict.index if "conc" in val]
        dnas = [np.unique(self.meta_dict.loc[k]) for k in dna_keys]
        all_dnas = []
        for dna in dnas:
            all_dnas += list(dna)
        
        # Ask for dna, inducers and signals
        await self.send(text_data=json.dumps({
                'type': 'input_requests',
                'data': {
                    'dna': all_dnas,
                    'inducer': inds,
                    'signal': signal_names[:-1]
                }
            }))


    async def parse_metadata(self, metadata):
        print(f"metadata: {metadata}", flush=True)
        # Do stuff with the excel
        wb = opxl.load_workbook(filename=io.BytesIO(self.file_binary), data_only=True)
        ws = wb['Data']
        signal_names = synergy_get_signal_names(ws)
        
        print(f"signal_names in metadata: {signal_names}", flush=True)
        
        # get dnas and inducers
        # meta_dict = synergy_load_meta(wb, self.columns)
        #meta_dict = meta_dict_mem[0]
        signal_map = {}

        print(f"metadata.keys(): {metadata.keys()}", flush=True)

        for i, s_id in enumerate(metadata['signal']):
            signal_map[signal_names[i]] = Signal.objects.get(id=s_id).name

        print(f"signal_map: {signal_map}", flush=True)

        dfs = synergy_load_data(ws, signal_names, signal_map)
        
        print(f"self.assay_id: {self.assay_id}", flush=True)
        start = time.time()
        upload_data(self.assay_id, self.meta_dict, dfs, {})
        end = time.time()
        print(f"FINISHED UPLOADING. Took {end-start} secs")
        await self.send(text_data=json.dumps({
                'type': 'creation_done'
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
