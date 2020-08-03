from django.urls import path
from flapjack_api.channels_middleware import TokenAuthMiddleware
from channels.routing import ProtocolTypeRouter, URLRouter
from .consumers import RegistryConsumer

websockets = ProtocolTypeRouter({
    "websocket": TokenAuthMiddleware(
        URLRouter([
            path(
                "upload", RegistryConsumer,
                name="registry-ws",
            ),
        ])
    ),
})
