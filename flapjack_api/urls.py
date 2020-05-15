from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('registry.urls')),
    path('jwtauth/', include('jwtauth.urls'), name='jwtauth'),
]
