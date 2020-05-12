from django.contrib import admin
from core.models import *

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