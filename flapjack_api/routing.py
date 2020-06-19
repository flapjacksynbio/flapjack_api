from channels.routing import ProtocolTypeRouter, URLRouter
from registry.routing import websockets

application = ProtocolTypeRouter({
    "websocket": websockets,
})
