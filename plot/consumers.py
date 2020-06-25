# Built in imports.
import json
import asyncio
# Third Party imports.
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer
from . import plotting
import pandas as pd

def fake_data():
    t = list(range(100))
    y1 = [v*v for v in t]
    y2 = [(100-v)*(100-v) for v in t]
    y3 = [(50-v)**3 for v in t]
    y4 = [(50-v)**4 for v in t]
    ys = [y1, y2, y3, y4]
    labels1 = ['apples', 'pears', 'oranges', 'bananas']
    labels2 = ['green', 'green', 'green', 'yellow']
    df = pd.DataFrame()
    for label1,label2,y in zip(labels1, labels2, ys):
        for tt,val in zip(t,y):
            data = {
                'time': tt,
                'value': val,
                'label1': label1,
                'label2': label2
            }   
            df = df.append(data, ignore_index=True)
    return df

class PlotConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add(
            "asd",
            self.channel_name
        )

        # await self.channel_layer.group_send(
        #     "asd",
        #     {
        #         'type': 'update_load_status',
        #     }
        # )

    async def update_load_status(self, event):
        # Here helper function fetches live score from DB.
        for i in range(1, 101):
            await self.send(text_data=json.dumps({
                'loaded': i
            }))
            await asyncio.sleep(0.1)

    async def generate_data(self, event):
        df = fake_data()
        traces, n_subplots = plotting.plot(df, groupby1='label2', groupby2='label1')
        if traces:
            await self.send(text_data=json.dumps({
                'type': 'plot_data',
                'data': {
                    'n_subplots': n_subplots,
                    'traces': traces
                }
            }))
        else:
            print('No traces to plot', flush=True)
            print(df.head())

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data['type'] == 'plot':
            await self.generate_data({'params': data['parameters']})

    async def websocket_disconnect(self, message):
        await self.channel_layer.group_discard(
            self.channel_name
        )
