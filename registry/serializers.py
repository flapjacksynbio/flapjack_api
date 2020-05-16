from rest_framework import serializers
from .models import Assay, Dna, Inducer, Measurement, Media, Sample, Signal, Strain, Study


class StudySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Study
        #fields = '__all__'
        fields = ('id', 'name', 'description', 'doi')


class AssaySerializer(serializers.HyperlinkedModelSerializer):
    #study = serializers.StringRelatedField()
    class Meta:
        model = Assay
        #fields = '__all__'
        fields = ('id', 'name', 'description',
                  'study', 'temperature', 'machine')


class SampleSerializer(serializers.HyperlinkedModelSerializer):
    #assay = serializers.StringRelatedField()
    class Meta:
        model = Sample
        #fields = '__all__'
        fields = ('id', 'row', 'col', 'assay', 'dna',
                  'media', 'strain', 'inducer')


class DnaSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Dna
        #fields = '__all__'
        fields = ('id', 'names', 'sboluris')


class MediaSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Media
        #fields = '__all__'
        fields = ('id', 'name', 'description', 'url')


class StrainSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Strain
        #fields = '__all__'
        fields = ('id', 'name', 'description', 'url')


class InducerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Inducer
        #fields = '__all__'
        fields = ('id', 'names', 'concentrations')


class MeasurementSerializer(serializers.HyperlinkedModelSerializer):
    #study = serializers.SerializerMethodField()
    #assay = serializers.SerializerMethodField()
    #dna = serializers.SerializerMethodField()
    #media = serializers.SerializerMethodField()
    #strain = serializers.SerializerMethodField()
    #inducer = serializers.SerializerMethodField()

    class Meta:
        model = Measurement
        #fields = '__all__'
        fields = (
            'id', 'signal', 'value', 'time', 'sample',
            # 'study',
            # 'assay',
            # 'dna',
            # 'media',
            # 'strain',
            # 'inducer'
        )
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
    class Meta:
        model = Signal
        #fields = '__all__'
        fields = ('id', 'name', 'description')


'''
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'url')

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('name', 'url')

class UserProfileInfoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = UserProfileInfo
        fields = '__all__'
'''
