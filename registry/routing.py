from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter
from flapjack_api.channels_middleware import TokenAuthMiddleware
from .consumers import UploadConsumer, MeasurementsConsumer


websockets = ProtocolTypeRouter({
    "websocket": TokenAuthMiddleware(
        URLRouter([
            path(
                "upload", UploadConsumer.as_asgi(),
                name="upload-ws",
            ),
            path(
                "measurements", MeasurementsConsumer.as_asgi(),
                name="measurements-ws",
            ),
        ])
    ),
})
