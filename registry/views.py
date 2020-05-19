from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import FilterSet, DjangoFilterBackend, CharFilter, NumberFilter
from .models import Assay, Dna, Inducer, Measurement, Media, Sample, Signal, Strain, Study
from .serializers import AssaySerializer, DnaSerializer, InducerSerializer, MeasurementSerializer, MediaSerializer, SampleSerializer, SignalSerializer, StrainSerializer, StudySerializer
from .permissions import AssayPermission, DnaPermission, MeasurementPermission, MediaPermission, SamplePermission, StrainPermission, StudyPermission


class StudyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows studies to be viewed or edited.
    """
    permission_classes = [StudyPermission]
    queryset = Study.objects.all()
    serializer_class = StudySerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_fields = ['name', 'doi']
    search_fields = ['name', 'doi', 'description']

    '''
    def get_queryset(self):
        user = self.request.user
        return get_objects_for_user(user, 'LoadData.view_study')

    def perform_create(self, serializer):
        obj = serializer.save()
        assign_perm('view_study', self.request.user, obj)
    '''


class AssayViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows assays to be viewed or edited.
    """
    permission_classes = [AssayPermission]
    queryset = Assay.objects.all()
    serializer_class = AssaySerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_fields = ['name', 'temperature', 'machine', 'study']
    search_fields = [
        'name',
        'machine',
        'temperature',
        'description',
        'study__name',
        'study__description'
    ]

    '''
    def get_queryset(self):
        user = self.request.user
        studies = get_objects_for_user(user, 'LoadData.view_study')
        return Assay.objects.filter(study__in=studies)
    '''


class SampleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows samples to be viewed or edited.
    """
    permission_classes = [SamplePermission]
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_fields = ['media', 'strain', 'dna', 'assay', 'assay__study']
    search_fields = [
        'media__name',
        'assay__name',
        'assay__description',
        'assay__study__name',
        'assay__study__description',
        'dna__names'
    ]

    '''
    def get_queryset(self):
        user = self.request.user
        studies = get_objects_for_user(user, 'LoadData.view_study')
        return Sample.objects.filter(assay__study__in=studies)
    '''


class DnaFilter(FilterSet):
    names = CharFilter(lookup_expr='icontains')
    sboluris = CharFilter(lookup_expr='icontains')

    class Meta:
        model = Dna
        fields = ('sboluris', 'names')


class DnaViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows dnas to be viewed or edited.
    """
    permission_classes = [DnaPermission]
    queryset = Dna.objects.all()
    serializer_class = DnaSerializer
    filterset_class = DnaFilter
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_fields = {
        'names': ['icontains'],
        'sboluris': ['icontains'],
        'assays': ['exact']
    }
    search_fields = [
        'names',
        'sboluris'
    ]

    '''
    def get_queryset(self):
        user = self.request.user
        studies = get_objects_for_user(user, 'LoadData.view_study')
        return Dna.objects.filter(assays__study__in=studies).distinct()
    '''


class MediaViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows media to be viewed or edited.
    """
    permission_classes = [MediaPermission]
    queryset = Media.objects.all()
    serializer_class = MediaSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_fields = ['name', 'description']
    search_fields = ['name', 'description']

    '''
    def get_queryset(self):
        user = self.request.user
        studies = get_objects_for_user(user, 'LoadData.view_study')
        return Media.objects.filter(assays__study__in=studies).distinct()
    '''


class StrainViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows strain to be viewed or edited.
    """
    permission_classes = [StrainPermission]
    queryset = Strain.objects.all()
    serializer_class = StrainSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_fields = ['name', 'description']
    search_fields = ['name', 'description']

    '''
    def get_queryset(self):
        user = self.request.user
        studies = get_objects_for_user(user, 'LoadData.view_study')
        return Strain.objects.filter(assays__study__in=studies).distinct()
    '''


class InducerFilter(FilterSet):
    names = CharFilter(lookup_expr='icontains')
    concentrations = NumberFilter(lookup_expr='icontains')

    class Meta:
        model = Inducer
        fields = ('names', 'concentrations')


class InducerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows inducers to be viewed or edited.
    """
    queryset = Inducer.objects.all()
    serializer_class = InducerSerializer
    filterset_class = InducerFilter
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_fields = {
        'names': ['icontains'],
        'concentrations': ['icontains']
    }
    search_fields = [
        'names',
        'concentrations'
    ]

    # def get_queryset(self):
    #    user = self.request.user
    #    studies = get_objects_for_user(user, 'LoadData.view_study')
    #    return Inducer.objects.filter(samples__assays__study__in=studies)


class MeasurementViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows measurements to be viewed or edited.
    """
    permission_classes = [MeasurementPermission]
    queryset = Measurement.objects.all()
    serializer_class = MeasurementSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_fields = ['signal', 'time',
                        'value', 'sample', 'sample__assay__name']
    search_fields = ['signal', 'sample__assay__name']

    """
    def list(self, request):
        start = time.time()
        #qs = self.get_queryset()
        #qs = self.filter_queryset(qs)
        #df = read_frame(qs)
        
        samples = Sample.objects.all() #filter(assay__name='RV7 - python')
        
        m = Measurement.objects.prefetch_related('sample__id') \
                                .prefetch_related('sample__assay__name') \
                                .prefetch_related('sample__assay__study__name') \
                                .prefetch_related('sample__media__name') \
                                .prefetch_related('sample__strain__name') \
                                .prefetch_related('sample__dna__names') \
                                .prefetch_related('sample__inducer__names') \
                                .prefetch_related('sample__inducer__concentrations') \
                                .prefetch_related('sample__row') \
                                .prefetch_related('sample__col') \
                                .filter(sample__in=samples)
        '''
        df = read_frame(m, fieldnames=['name', \
                                        'value', \
                                        'time', \
                                        'sample__id', \
                                        'sample__assay__name', \
                                        'sample__assay__study__name', \
                                        'sample__media__name', \
                                        'sample__strain__name', \
                                        'sample__dna__names', \
                                        'sample__inducer__names', \
                                        'sample__inducer__concentrations', \
                                        'sample__row', 'sample__col'])
        
        json_df = json.loads(df.to_json())
        '''
        end = time.time()
        print('list took %f seconds'%(end-start), flush=True)
        return Response('')
    """
    '''
    def get_queryset(self):
        user = self.request.user
        studies = get_objects_for_user(user, 'LoadData.view_study')
        return Measurement.objects.filter(sample__assay__study__in=studies)
    '''


class SignalViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows signals to be viewed or edited.
    """
    queryset = Signal.objects.all()
    serializer_class = SignalSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_fields = ['name', 'description']
    search_fields = ['name', 'description']

    '''
    def get_queryset(self):
        user = self.request.user
        studies = get_objects_for_user(user, 'LoadData.view_study')
        return Signal.objects.filter(study__in=studies)
    '''


'''
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_fields = ['username']
    search_fields = ['username']

class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_fields = ['name']
    search_fields = ['name']

class UserProfileInfoViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = UserProfileInfo.objects.all()
    serializer_class = UserProfileInfoSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_fields = ['user', 'portfolio_site']
    search_fields = ['user', 'portfolio_site']
'''
