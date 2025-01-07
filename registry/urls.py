from rest_framework import routers
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from . import views

router = routers.DefaultRouter()
router.register(r'study', views.StudyViewSet, basename='study')
router.register(r'assay', views.AssayViewSet, basename='assay')
router.register(r'sample', views.SampleViewSet, basename='sample')
router.register(r'dna', views.DnaViewSet, basename='dna')
router.register(r'media', views.MediaViewSet, basename='media')
router.register(r'strain', views.StrainViewSet, basename='strain')
router.register(r'measurement', views.MeasurementViewSet, basename='measurement')
router.register(r'signal', views.SignalViewSet, basename='signal')
router.register(r'supplement', views.SupplementViewSet, basename='supplement')
router.register(r'chemical', views.ChemicalViewSet, basename='chemical')
router.register(r'vector', views.VectorViewSet, basename='vector')
router.register(r'vectorall', views.VectorAllViewSet, basename='vectorall')
router.register(r'user', views.UserViewSet, basename='user')
router.register(r'assays_in_study', views.AssaysInStudy, basename='assays_in_study')
router.register(r'vector_in_assay', views.VectorInAssay, basename='vector_in_assay')
router.register(r'strain_in_assay', views.StrainInAssay, basename='strain_in_assay')
router.register(r'media_in_assay', views.MediaInAssay, basename='media_in_assay')
router.register(r'signal_in_assay', views.SignalInAssay, basename='signal_in_assay')


urlpatterns = [
    url(r'^api/', include(router.urls))
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
