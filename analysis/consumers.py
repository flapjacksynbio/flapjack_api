# Built in imports.
import json
import asyncio
# Third Party imports.
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer
from . import analysis
from registry.util import get_samples, get_measurements
from plotly.subplots import make_subplots
import plotly
import pandas as pd
import time
import math

class AnalysisConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        print(self.user)
        await self.accept()
        await self.channel_layer.group_add(
            "analysis",
            self.channel_name
        )
        
    async def receive(self, text_data):
        print(f"Receive. text_data: {text_data}", flush=True)
        data = json.loads(text_data)
        if data['type'] == 'analysis':
            print(data, flush=True)
            #await self.generate_data({'params': data['parameters']})

    async def disconnect(self, message):
        await self.channel_layer.group_discard(
            "analysis",
            self.channel_name
        )
