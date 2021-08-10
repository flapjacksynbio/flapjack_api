from channels.routing import ProtocolTypeRouter, URLRouter
from plot.routing import websockets as plotWs
from analysis.routing import websockets as analysisWs
from registry.routing import websockets as uploadWs

from django.conf.urls import url
from channels.auth import AuthMiddlewareStack

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
            URLRouter([
            url('^ws/plot', plotWs),
            url('^ws/analysis', analysisWs),
            url('^ws/registry', uploadWs)
        ])
    ),
})
