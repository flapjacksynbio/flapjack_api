from registry.models import *
from django_pandas.io import read_frame
import time

def get_samples(filter):
    print('get_samples', flush=True)
    start = time.time()
    print(f"filter: {filter}", flush=True)
    studies = filter.get('studyIds')
    assays = filter.get('assayIds')
    vectors = filter.get('vectorIds')
    meds = filter.get('mediaIds')
    strains = filter.get('strainIds')

    s = Sample.objects.all()
    filter_exist = False

    if studies:
        s = s.filter(assay__study__id__in=studies)
        filter_exist = True    
    if assays:
        s = s.filter(assay__id__in=assays)
        filter_exist = True    
    if vectors:
        s = s.filter(vector__id__in=vectors)
        filter_exist = True    
    if meds:
        s = s.filter(media__id__in=meds)  
        filter_exist = True    
    if strains:
        s = s.filter(strain__id__in=strains)
        filter_exist = True    

    if not filter_exist:
        s = Sample.objects.none()

    end = time.time()
    print('get_samples took %f seconds'%(end-start), flush=True)
    return s

# Get dataframe of measurement values for a set of samples in a query
# -----------------------------------------------------------------------------------
def get_measurements(samples):
    # Get measurements for a given samples
    print('get_measurements', flush=True)
    start = time.time()
    samp_ids = [samp.id for samp in samples]
    m = Measurement.objects.filter(sample__id__in=samp_ids)
    df = read_frame(m, fieldnames=['signal__id', \
                                    'value', \
                                    'time', \
                                    'sample__id', \
                                    'sample__assay__id', \
                                    'sample__assay__study__id', \
                                    'sample__media__id', \
                                    'sample__strain__id', \
                                    'sample__vector__id', \
                                    'sample__supplements', \
                                    #'sample__supplement__concentrations', \
                                    'sample__row', 'sample__col'])
    end = time.time()
    print('get_measurements took ', end-start, flush=True)
    return df