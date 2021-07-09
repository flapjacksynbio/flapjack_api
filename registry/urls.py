from rest_framework import routers
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from . import views

router = routers.DefaultRouter()
router.register(r'study', views.StudyViewSet)
router.register(r'assay', views.AssayViewSet)
router.register(r'sample', views.SampleViewSet)
router.register(r'dna', views.DnaViewSet)
router.register(r'media', views.MediaViewSet)
router.register(r'strain', views.StrainViewSet)
router.register(r'measurement', views.MeasurementViewSet)
router.register(r'signal', views.SignalViewSet)
router.register(r'supplement', views.SupplementViewSet)
router.register(r'chemical', views.ChemicalViewSet)
router.register(r'vector', views.VectorViewSet)
router.register(r'vectorall', views.VectorAllViewSet)
router.register(r'user', views.UserViewSet)
router.register(r'assays_in_study', views.AssaysInStudy)
router.register(r'vector_in_assay', views.VectorInAssay)
router.register(r'strain_in_assay', views.StrainInAssay)
router.register(r'media_in_assay', views.MediaInAssay)
router.register(r'signal_in_assay', views.SignalInAssay)


urlpatterns = [
    url(r'^api/', include(router.urls))
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
