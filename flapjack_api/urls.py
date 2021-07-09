from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('registry.urls')),
    path('api/auth/', include('accounts.urls'), name='accounts'),
    path('admin/', admin.site.urls),
]