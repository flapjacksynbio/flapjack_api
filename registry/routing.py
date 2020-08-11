from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter

from .consumers import UploadConsumer, MeasurementsConsumer
websockets = URLRouter([
    path(
        "upload", UploadConsumer,
        name="upload-ws",
    ),
    path(
        "measurements", MeasurementsConsumer,
        name="measurements-ws",
    ),        
])
