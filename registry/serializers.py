from rest_framework import serializers
from .models import Assay, Dna, Inducer, Measurement, Media, Sample, Signal, Strain, Study


class StudySerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    class Meta:
        model = Study
        fields = '__all__'

class AssaySerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    class Meta:
        model = Assay
        fields = '__all__'

class SampleSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    class Meta:
        model = Sample
        fields = '__all__'

class DnaSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    class Meta:
        model = Dna
        fields = '__all__'

class MediaSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    class Meta:
        model = Media
        fields = '__all__'

class StrainSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    class Meta:
        model = Strain
        fields = '__all__'

class InducerSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    class Meta:
        model = Inducer
        fields = '__all__'

class MeasurementSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    class Meta:
        model = Measurement
        fields = '__all__'
        '''
        fields = (
            'id', 'signal', 'value', 'time', 'sample',
            'study',
            'assay',
            'dna',
            'media',
            'strain',
            'inducer'
        )
        '''
    '''
    def get_study(self, obj):
        return obj.sample.assay.study.name
    def get_assay(self, obj):
        return obj.sample.assay.name
    def get_dna(self, obj):
        return obj.sample.dna.names
    def get_media(self, obj):
        return obj.sample.media.name
    def get_strain(self, obj):
        return obj.sample.strain.name
    def get_inducer(self, obj):
        return obj.sample.inducer.names
    '''


class SignalSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    class Meta:
        model = Signal
        fields = '__all__'
        
'''
class UserSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    class Meta:
        model = User
        fields = '__all__'

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    class Meta:
        model = Group
        fields = '__all__'

class UserProfileInfoSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    class Meta:
        model = UserProfileInfo
        fields = '__all__'
'''
