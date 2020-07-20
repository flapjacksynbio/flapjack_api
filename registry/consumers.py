# Built in imports.
import json
import asyncio
import io
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
columns = [x+str(y) for x in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'] for y in range(1,13)]
file_binary = []
meta_dict_mem = []

class RegistryConsumer(AsyncWebsocketConsumer): 
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add(
            "upload",
            self.channel_name
        )

    # TO DO: setup message receiving and disconnection
    async def initialize_upload(self, data):
        print(data)

        # Do stuff with the data (study id, assay data, etc...)

        # create assay, how to send id ???
        assay = Assay(study=Study.objects.get(id=data['study']), 
                    name=data['name'], 
                    machine="HTX Synergy", 
                    description=data['description'], 
                    temperature=float(data['temperature']),
                    owner=User.objects.get(username='guillermo'))
        assay.save()
        # Send message for receiving file
        await self.send(text_data=json.dumps({
                'type': 'ready_for_file'
            }))


    async def read_binary(self, bin_data):
        print(f"type(columns): {type(columns)}", flush=True)
        print(f"type(file_binary): {type(file_binary)}", flush=True)

        file_binary.append(bin_data)

        # Do stuff with the excel
        wb = opxl.load_workbook(filename=io.BytesIO(bin_data), data_only=True)
        ws = wb['Data']
        #assay_name = os.path.splitext(file_name)[0], 
        signal_names = synergy_get_signal_names(ws)
        
        #print(f"assay_name: {assay_name}", flush=True)
        print(f"signal_names: {signal_names}", flush=True)
        
        # get dnas and inducers
        meta_dict = synergy_load_meta(wb, columns)
        meta_dict_mem.append(meta_dict)
        dnas = []
        inds = []
        for val in meta_dict.index:
            if "DNA" in val:
                dnas.append(val)
            elif "conc" in val:
                inds.append(val)

        #dfs = synergy_load_data(ws, signal_names, signal_map)
        
        # Ask for dna, inducers and signals
        await self.send(text_data=json.dumps({
                'type': 'input_requests',
                'data': {
                    'dna': dnas,
                    'inducer': inds,
                    'signal': signal_names[:-1]
                }
            }))


    async def parse_metadata(self, metadata):
        print(f"metadata: {metadata}", flush=True)
        # Do stuff with the excel
        wb = opxl.load_workbook(filename=io.BytesIO(file_binary[0]), data_only=True)
        ws = wb['Data']
        signal_names = synergy_get_signal_names(ws)
        
        print(f"signal_names in metadata: {signal_names}", flush=True)
        
        # get dnas and inducers
        # meta_dict = synergy_load_meta(wb, columns)
        meta_dict = meta_dict_mem[0]
        print(f"meta_dict.keys(): {meta_dict.keys()}")
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
