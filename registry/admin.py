from django.contrib import admin
from registry.models import Assay, Dna, Inducer, Measurement, Media, Sample, Signal, Strain, Study

# Models modifiable in the admin
admin.site.register(Study)
admin.site.register(Assay)
admin.site.register(Strain)
admin.site.register(Media)
admin.site.register(Dna)
admin.site.register(Sample)
admin.site.register(Measurement)
admin.site.register(Inducer)
admin.site.register(Signal)
