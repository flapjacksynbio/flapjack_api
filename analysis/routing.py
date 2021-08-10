from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter
from flapjack_api.channels_middleware import TokenAuthMiddleware
from .consumers import AnalysisConsumer


websockets = ProtocolTypeRouter({
    "websocket": TokenAuthMiddleware(
        URLRouter([
            path(
                "analysis", AnalysisConsumer.as_asgi(),
                name="analysis-ws",
            ),
        ])
    ),
})
