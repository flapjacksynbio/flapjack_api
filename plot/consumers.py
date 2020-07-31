# Built in imports.
import json
import asyncio
# Third Party imports.
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer
from . import plotting
from plotly.subplots import make_subplots
import plotly
import pandas as pd
import time

group_fields = {
    'Vector': 'sample__vector__name',
    'Study': 'sample__assay__study__name',
    'Signal': 'signal__name',
    'Assay': 'sample__assay__name',
    'Media': 'sample__media__name', 
    'Strain': 'sample__strain__name', 
    'Supplement': 'sample__supplements'
}

class PlotConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        print(self.user)
        await self.accept()
        await self.channel_layer.group_add(
            "asd",
            self.channel_name
        )

    async def plot(self, df, mean=False, std=False, normalize=False, groupby1=None, groupby2=None):
        '''
            Generate plot data for frontend plotly plot generation
        '''
        n_measurements = len(df)
        if n_measurements == 0:
            return None

        traces = []
        axis = 1
        colors = {}
        colidx = 0
        groupby1 = group_fields[groupby1]
        groupby2 = group_fields[groupby2]
        grouped = df.groupby(groupby1)     
        n_subplots = len(grouped)
        ncolors = len(plotting.palette)
        progress = 0
        for name1,g1 in grouped:
            for name2,g2 in g1.groupby(groupby2):
                if name2 not in colors:
                    colors[name2] = plotting.palette[colidx%ncolors]
                    colidx += 1
                    show_legend_group = True
                else:
                    show_legend_group = False

                traces += plotting.make_traces(
                        g2,
                        color=colors[name2], 
                        mean=mean, 
                        std=std, 
                        normalize=normalize,
                        show_legend_group=show_legend_group,
                        group_name=name2,
                        xaxis='x%d'%axis, yaxis='y%d'%axis 
                    )  
                progress += len(g2)
                print(progress/n_measurements)
                await self.send(text_data=json.dumps({
                    'type': 'progress_update',
                    'data': {'progress': int(100*progress/n_measurements)}
                }))
                await asyncio.sleep(0)
            axis += 1
        return traces, n_subplots

    async def generate_data(self, event):
        params = event['params']
        plot_options = params['plotOptions']
        s = plotting.get_samples(params)
        n_samples = s.count()
        if n_samples > 0:
            df = plotting.get_measurements(s)
            #df = await self.fake_data(event)
            subplots = plot_options['subplots']
            markers = plot_options['markers']
            mean = 'Mean' in plot_options['plot']
            std = 'std' in plot_options['plot']
            traces, n_subplots = await self.plot(df, 
                                                groupby1=subplots, 
                                                groupby2=markers,
                                                mean=mean, std=std
                                                )
        else:
            print('No samples found for query params', flush=True)
            traces, n_subplots = [], 0
        # Send back traces to plot
        await self.send(text_data=json.dumps({
            'type': 'plot_data',
            'data': {
                'n_subplots': n_subplots,
                'traces': traces 
            }
        }))
        
    async def receive(self, text_data):
        print(f"Receive. text_data: {text_data}", flush=True)
        data = json.loads(text_data)
        if data['type'] == 'plot':
            await self.generate_data({'params': data['parameters']})

    async def disconnect(self, message):
        await self.channel_layer.group_discard(
            "asd",
            self.channel_name
        )
