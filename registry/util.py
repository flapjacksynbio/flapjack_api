from registry.models import *
from django_pandas.io import read_frame
import time

pretty_field_names = {
    'signal__id': 'Signal_id',
    'signal__name': 'Signal',
    'signal__color': 'Color',
    'value': 'Measurement',
    'time': 'Time',
    'sample__id': 'Sample',
    'sample__assay__name': 'Assay',
    'sample__assay__study__name': 'Study',
    'sample__media__name': 'Media',
    'sample__strain__name': 'Strain',
    'sample__vector__name': 'Vector',
    'sample__supplements__name': 'Supplement',
    'sample__supplements__chemical__name': 'Chemical',
    'sample__supplements__chemical__id': 'Chemical_id',
    'sample__supplements__concentration': 'Concentration',
    'sample__row': 'Row', 
    'sample__col': 'Column'
}

def get_samples(filter):
    print('get_samples', flush=True)
    start = time.time()
    print(f"filter: {filter}", flush=True)
    studies = filter.get('study')
    assays = filter.get('assay')
    vectors = filter.get('vector')
    meds = filter.get('media')
    strains = filter.get('strain')

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
def get_measurements(samples, signals=None):
    # Get measurements for a given samples
    print('get_measurements', flush=True)
    start = time.time()
    samp_ids = [samp.id for samp in samples]
    m = Measurement.objects.filter(sample__id__in=samp_ids)
    # Filter by signal
    if signals:
        m = m.filter(signal__id__in=signals)
    # Get pandas dataframe 
    df = read_frame(m, fieldnames=['signal__id',
                                    'signal__color',
                                    'signal__name', \
                                    'value', \
                                    'time', \
                                    'sample__id', \
                                    'sample__assay__name', \
                                    'sample__assay__study__name', \
                                    'sample__media__name', \
                                    'sample__strain__name', \
                                    'sample__vector__name', \
                                    'sample__supplements__name', \
                                    'sample__supplements__chemical__name', \
                                    'sample__supplements__chemical__id', \
                                    'sample__supplements__concentration', \
                                    'sample__row', 'sample__col'])
    df.columns = [pretty_field_names[col] for col in df.columns]
    end = time.time()
    print('get_measurements took ', end-start, flush=True)
    return df