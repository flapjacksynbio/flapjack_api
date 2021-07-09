from django.contrib import admin
from registry.models import *

# Models modifiable in the admin
admin.site.register(Study)
admin.site.register(Assay)
admin.site.register(Strain)
admin.site.register(Media)
admin.site.register(Dna)
admin.site.register(Sample)
admin.site.register(Measurement)
admin.site.register(Vector)
admin.site.register(Chemical)
admin.site.register(Supplement)
admin.site.register(Signal)
