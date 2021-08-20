from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter
from flapjack_api.channels_middleware import TokenAuthMiddleware
from .consumers import SBOLConsumer, UploadConsumer, MeasurementsConsumer, SBOLConsumer


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
            path(
                "sbol_doc", SBOLConsumer.as_asgi(),
                name="sbol_doc-ws",
            ),
        ])
    ),
})
