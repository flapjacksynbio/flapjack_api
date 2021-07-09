from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter
from flapjack_api.channels_middleware import TokenAuthMiddleware
from .consumers import UploadConsumer, MeasurementsConsumer


websockets = ProtocolTypeRouter({
    "websocket": TokenAuthMiddleware(
        URLRouter([
            path(
                "upload", UploadConsumer,
                name="upload-ws",
            ),
            path(
                "measurements", MeasurementsConsumer,
                name="measurements-ws",
            ),
        ])
    ),
})
