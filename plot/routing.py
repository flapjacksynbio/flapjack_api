from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter

from .consumers import PlotConsumer
websockets = URLRouter([
    path(
        "plot", PlotConsumer,
        name="plot-ws",
    ),
])
