from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import registration, log_in

urlpatterns = [
    path('register/', registration, name='register'),
    path('log_in/', log_in, name='log_in'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
