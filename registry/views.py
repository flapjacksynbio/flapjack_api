from django.db.models import Q
from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from rest_framework_filters import FilterSet, CharFilter, NumberFilter, RelatedFilter, BooleanFilter
from rest_framework_filters.backends import RestFrameworkFilterBackend
from .models import *
from .serializers import *
from .permissions import *
import django_filters


# FilterSets

class DnaFilter(FilterSet):
    name = CharFilter(lookup_expr='icontains')
    sboluri = CharFilter(lookup_expr='icontains')

    class Meta:
        model = Dna
        fields = ('id', 'sboluri', 'name')


class MediaFilter(FilterSet):
    name = CharFilter(lookup_expr='icontains')
    description = CharFilter(lookup_expr='icontains')

    class Meta:
        model = Media
        fields = ('id', 'name', 'description')


class StrainFilter(FilterSet):
    name = CharFilter(lookup_expr='icontains')
    description = CharFilter(lookup_expr='icontains')

    class Meta:
        model = Strain
        fields = ('id', 'name', 'description')


class StudyFilter(FilterSet):
    name = CharFilter(lookup_expr='icontains')
    doi = CharFilter(lookup_expr='icontains')
    is_owner = BooleanFilter(field_name='owner', method='filter_is_owner')

    class Meta:
        model = Study
        fields = ('id', 'name', 'doi')

    def filter_is_owner(self, qs, name, value):
        user = self.request.user
        return Study.objects.filter(owner=user)


class AssayFilter(FilterSet):
    name = CharFilter(lookup_expr='icontains')
    temperature = NumberFilter(lookup_expr='exact')
    machine = CharFilter(lookup_expr='icontains')
    study = RelatedFilter(StudyFilter, field_name='study',
                          queryset=Study.objects.all())

    class Meta:
        model = Assay
        fields = ('id', 'name', 'temperature', 'machine')


class ChemicalFilter(FilterSet):
    name = CharFilter(lookup_expr='icontains')
    description = CharFilter(lookup_expr='icontains')
    description = NumberFilter(lookup_expr='exact')

    class Meta:
        model = Chemical
        fields = ('id', 'name','description','pubchemid')


class VectorFilter(FilterSet):
    dnas = RelatedFilter(DnaFilter, field_name='dnas',
                        queryset=Dna.objects.all())
    sboluri = RelatedFilter(DnaFilter, field_name='dnas__sboluri',
                        queryset=Dna.objects.all(), lookup_expr='icontains')
    class Meta:
        model = Vector
        fields = ('id', 'name','dnas','sboluri')


class SupplementFilter(FilterSet):
    chemical = RelatedFilter(ChemicalFilter, field_name='chemical',
                            queryset=Chemical.objects.all())
    concentration = NumberFilter(lookup_expr='exact')

    class Meta:
        model = Supplement
        fields = ('id', 'concentration',)


class SampleFilter(FilterSet):
    assay = RelatedFilter(AssayFilter, field_name='assay',
                          queryset=Assay.objects.all())
    media = RelatedFilter(MediaFilter, field_name='media',
                          queryset=Media.objects.all())
    vector = RelatedFilter(VectorFilter, field_name='vector',
                        queryset=Dna.objects.all())
    supplements = RelatedFilter(SupplementFilter, field_name='supplements',
                        queryset=Supplement.objects.all())
    temperature = NumberFilter(lookup_expr='exact')
    machine = CharFilter(lookup_expr='icontains')

    class Meta:
        model = Sample
        fields = ('id', 'temperature', 'machine')


class SignalFilter(FilterSet):
    name = CharFilter(lookup_expr='icontains')
    description = CharFilter(lookup_expr='icontains')

    class Meta:
        model = Signal
        fields = ('id', 'name', 'description')


class MeasurementFilter(FilterSet):
    sample = RelatedFilter(SampleFilter, field_name='sample',
                           queryset=Sample.objects.all())
    signal = RelatedFilter(SignalFilter, field_name='signal',
                           queryset=Signal.objects.all())
    value = NumberFilter(lookup_expr='exact')

    class Meta:
        model = Measurement
        fields = ('id', 'value')


# ViewSets

class StudyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows studies to be viewed or edited.
    """
    permission_classes = [StudyPermission]
    queryset = Study.objects.all()
    serializer_class = StudySerializer
    filter_backends = [SearchFilter, RestFrameworkFilterBackend]
    filterset_class = StudyFilter
    search_fields = ['name', 'doi', 'description']

    def get_queryset(self):
        user = self.request.user
        return Study.objects.filter(Q(owner=user) | Q(public=True) | Q(shared_with=user))

    '''
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
    filter_backends = [SearchFilter, RestFrameworkFilterBackend]
    filterset_class = AssayFilter
    search_fields = [
        'name',
        'temperature',
        'machine',
        'description',
        'study__name',
        'study__description'
    ]

    def get_queryset(self):
        user = self.request.user
        return Assay.objects.filter(
            Q(study__owner=user) |
            Q(study__public=True) |
            Q(study__shared_with=user)
        )


class SampleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows samples to be viewed or edited.
    """
    permission_classes = [SamplePermission]
    queryset = Sample.objects.all()
    #serializer_class = SampleSerializer
    filter_backends = [SearchFilter, RestFrameworkFilterBackend]
    filter_class = SampleFilter
    search_fields = [
        'media__name',
        'assay__name',
        'assay__description',
        'assay__study__name',
        'assay__study__description',
        'vector__dnas'
    ]

    def get_serializer_class(self):
        if self.action == 'create':
            return SampleSerializerCreate
        else:
            return SampleSerializer

    def get_queryset(self):
        user = self.request.user
        return Sample.objects.filter(
            Q(assay__study__owner=user) |
            Q(assay__study__public=True) |
            Q(assay__study__shared_with=user)
        ).distinct()

class DnaViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows dnas to be viewed or edited.
    """
    permission_classes = [DnaPermission]
    queryset = Dna.objects.all()
    serializer_class = DnaSerializer
    filterset_class = DnaFilter
    filter_backends = [SearchFilter, RestFrameworkFilterBackend]
    search_fields = [
        'name',
        'sboluri'
    ]

    def get_queryset(self):
        user = self.request.user
        return Dna.objects.filter(
            Q(vectors__sample__assay__study__owner=user) |
            Q(vectors__sample__assay__study__public=True) |
            Q(vectors__sample__assay__study__shared_with=user)
        ).distinct()


class MediaViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows media to be viewed or edited.
    """
    permission_classes = [MediaPermission]
    queryset = Media.objects.all()
    serializer_class = MediaSerializer
    filter_backends = [SearchFilter, RestFrameworkFilterBackend]
    filter_class = MediaFilter
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
    filter_class = StrainFilter
    filter_backends = [SearchFilter, RestFrameworkFilterBackend]
    search_fields = ['name', 'description']

    '''
    def get_queryset(self):
        user = self.request.user
        studies = get_objects_for_user(user, 'LoadData.view_study')
        return Strain.objects.filter(assays__study__in=studies).distinct()
    '''


class VectorAllViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows vector to be viewed or edited.
    """
    permission_classes = [VectorPermission]
    queryset = Vector.objects.all()
    serializer_class = VectorAllSerializer
    filter_class = VectorFilter
    filter_backends = [SearchFilter, RestFrameworkFilterBackend]
    search_fields = ['name']

    def get_queryset(self):
        user = self.request.user
        return Vector.objects.filter(
            Q(sample__assay__study__owner=user) |
            Q(sample__assay__study__public=True) |
            Q(sample__assay__study__shared_with=user)
        ).distinct()


class VectorViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows vector to be viewed or edited.
    """
    permission_classes = [VectorPermission]
    queryset = Vector.objects.all()
    serializer_class = VectorSerializer
    filter_class = VectorFilter
    filter_backends = [SearchFilter, RestFrameworkFilterBackend]
    search_fields = ['name']

    def get_queryset(self):
        user = self.request.user
        return Vector.objects.filter(
            Q(sample__assay__study__owner=user) |
            Q(sample__assay__study__public=True) |
            Q(sample__assay__study__shared_with=user)
        ).distinct()

class SupplementViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows supplement to be viewed or edited.
    """
    permission_classes = [SupplementPermission]
    queryset = Supplement.objects.all()
    serializer_class = SupplementSerializer
    filter_class = SupplementFilter
    filter_backends = [SearchFilter, RestFrameworkFilterBackend]
    search_fields = ['chemical', 'concentration']


class ChemicalViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows chemical to be viewed or edited.
    """
    permission_classes = [ChemicalPermission]
    queryset = Chemical.objects.all()
    serializer_class = ChemicalSerializer
    filter_class = ChemicalFilter
    filter_backends = [SearchFilter, RestFrameworkFilterBackend]
    search_fields = ['name', 'description']

class MeasurementViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows measurements to be viewed or edited.
    """
    permission_classes = [MeasurementPermission]
    queryset = Measurement.objects.all()
    serializer_class = MeasurementSerializer
    filter_class = MeasurementFilter
    filter_backends = [SearchFilter, RestFrameworkFilterBackend]
    # filterset_fields = ['signal', 'time',
    #                    'value', 'sample', 'sample__assay__name']
    search_fields = ['signal', 'sample__assay__name', 'sample__assay__study__name']

    def get_queryset(self):
        user = self.request.user
        return Measurement.objects.filter(
            Q(sample__assay__study__owner=user) |
            Q(sample__assay__study__public=True) |
            Q(sample__assay__study__shared_with=user)
        ).distinct()

class SignalViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows signals to be viewed or edited.
    """
    queryset = Signal.objects.all()
    serializer_class = SignalSerializer
    filter_class = SignalFilter
    filter_backends = [SearchFilter, RestFrameworkFilterBackend]
    # filterset_fields = ['name', 'description']
    search_fields = ['name', 'description']

    '''
    def get_queryset(self):
        user = self.request.user
        studies = get_objects_for_user(user, 'LoadData.view_study')
        return Signal.objects.filter(study__in=studies)
    '''

