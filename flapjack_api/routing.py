from channels.routing import ProtocolTypeRouter, URLRouter
from plot.routing import websockets

application = ProtocolTypeRouter({
    "websocket": websockets,
})
