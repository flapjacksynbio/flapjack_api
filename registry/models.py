from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import User
from decimal import Decimal


class Study(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    doi = models.URLField(blank=True)
    owner = models.ForeignKey(
        'auth.User', related_name='studies', on_delete=models.CASCADE)
    shared_with = models.ManyToManyField(
        User, related_name='shared_studies', blank=True, default=list)
    public = models.BooleanField()

    def __str__(self):
        return self.name


class Assay(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    machine = models.CharField(max_length=100)
    description = models.TextField()
    temperature = models.FloatField()

    def __str__(self):
        return self.name


class Media(models.Model):
    owner = models.ForeignKey(
        'auth.User', related_name='medias', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name


class Strain(models.Model):
    owner = models.ForeignKey(
        'auth.User', related_name='strains', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name


class Chemical(models.Model):
    owner = models.ForeignKey(
        'auth.User', related_name='chemicals', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    pubchemid = models.IntegerField(null=True)

    def __str__(self):
        return self.name


class Supplement(models.Model):
    owner = models.ForeignKey(
        'auth.User', related_name='supplements', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    chemical = models.ForeignKey(Chemical, on_delete=models.CASCADE)
    concentration = models.FloatField()

    def __str__(self):
        return self.name


class Dna(models.Model):
    owner = models.ForeignKey(
        'auth.User', related_name='dnas', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    sboluri = models.URLField(blank=True)

    def __str__(self):
        return self.name


class Vector(models.Model):
    owner = models.ForeignKey(
        'auth.User', related_name='vectors', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    dnas = models.ManyToManyField(Dna, related_name='vectors')

    def __str__(self):
        return self.name

class Sample(models.Model):
    assay = models.ForeignKey(Assay, on_delete=models.CASCADE)
    media = models.ForeignKey(Media, null=True, on_delete=models.CASCADE)
    strain = models.ForeignKey(Strain, null=True, on_delete=models.CASCADE)
    vector = models.ForeignKey(Vector, null=True, on_delete=models.CASCADE)
    supplements = models.ManyToManyField(Supplement, related_name='samples')
    row = models.IntegerField()
    col = models.IntegerField()

    def __str__(self):
        return (f"Row: {self.row}, Col: {self.col}")


class Signal(models.Model):
    owner = models.ForeignKey(
        'auth.User', related_name='signals', on_delete=models.CASCADE)
    name = models.TextField()
    description = models.TextField()
    color = models.CharField(max_length=100, default='')        
    def __str__(self):
        return self.name


class Measurement(models.Model):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    signal = models.ForeignKey(Signal, on_delete=models.CASCADE)
    value = models.FloatField()
    time = models.FloatField()

    def __str__(self):
        return str(self.value)
