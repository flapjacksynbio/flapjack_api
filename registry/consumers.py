# Built in imports.
import json
import asyncio
import io
# Third Party imports.
import pandas as pd
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer

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

        # Send message for receiving file
        await self.send(text_data=json.dumps({
                'type': 'ready_for_file'
            }))

    async def read_binary(self, bin_data):
        to_read = io.BytesIO()
        to_read.write(bin_data)
        to_read.seek(0)
        
        df = pd.read_excel(to_read)
        print(df.head())
        
        # Do stuff with the excel

        # Ask for dnta, inducers and signals
        await self.send(text_data=json.dumps({
                'type': 'input_requests',
                'data': {
                    'dna': [
                        'dna1', 
                        'dna2'
                    ],
                    'inducer': [
                        'ind1',
                        'ind2',
                    ],
                    'signal': [
                        'sig1',
                        'sig2',
                    ]
                }
            }))

    async def parse_metadata(self, metadata):
        print(metadata)

        await self.send(text_data=json.dumps({
                'type': 'creation_done'
            }))


    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            data = json.loads(text_data)
            if data['type'] == 'init_upload':
                await self.initialize_upload(data['data'])
            elif data['type'] == 'metadata':
                await self.parse_metadata(data['data'])
        if bytes_data:
            print('received bytes data:', len(bytes_data))
            await self.read_binary(bytes_data)
        

    async def websocket_disconnect(self, message):
        await self.channel_layer.group_discard(
            "upload",
            self.channel_name
        )
