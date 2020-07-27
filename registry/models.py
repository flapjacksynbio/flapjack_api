from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import User


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
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name


class Strain(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name


class Dna(models.Model):
    names = ArrayField(models.CharField(max_length=100))
    sboluris = ArrayField(models.CharField(
        max_length=1000), blank=True, default=list)
    assays = models.ManyToManyField(Assay, related_name='dnas')

    def __str__(self):
        names = self.names
        names.sort()
        return ' + '.join(names)


class Inducer(models.Model):
    names = ArrayField(models.CharField(max_length=100))
    concentrations = ArrayField(models.FloatField())

    def __str__(self):
        return ' + '.join(self.names)


class Sample(models.Model):
    assay = models.ForeignKey(Assay, on_delete=models.CASCADE)
    media = models.ForeignKey(Media, on_delete=models.CASCADE)
    strain = models.ForeignKey(Strain, on_delete=models.CASCADE)
    dna = models.ForeignKey(Dna, on_delete=models.CASCADE)
    inducer = models.ForeignKey(
        Inducer, blank=True, null=True, on_delete=models.CASCADE)
    row = models.IntegerField()
    col = models.IntegerField()

    def __str__(self):
        return ("Row: {}, Col: {}".format(self.row, self.col))


class Signal(models.Model):
    name = models.TextField()
    description = models.TextField()

    def __str__(self):
        return self.name


class Measurement(models.Model):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    signal = models.ForeignKey(Signal, on_delete=models.CASCADE)
    value = models.FloatField()
    time = models.FloatField()

    def __str__(self):
        return self.value
