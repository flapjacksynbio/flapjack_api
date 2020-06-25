from channels.routing import ProtocolTypeRouter, URLRouter
from plot.routing import websockets as plotWs
from registry.routing import websockets as uploadWs

from django.conf.urls import url

application = ProtocolTypeRouter({
    "websocket": URLRouter([
        url('^ws/plot', plotWs),
        url('^ws/registry', uploadWs)
    ]),
})
