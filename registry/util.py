from registry.models import *
from django_pandas.io import read_frame
import time

field_names = [
    'signal__id',
    'signal__name',
    'signal__color',
    'value',
    'time',
    'sample__id',
    'sample__assay__name',
    'sample__assay__study__name',
    'sample__media__name',
    'sample__strain__name',
    'sample__vector__name',
    'sample__supplements__name',
    'sample__supplements__chemical__name',
    'sample__supplements__chemical__id',
    'sample__supplements__concentration',
    'sample__row', 
    'sample__col'
]

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
    df = read_frame(m, fieldnames=field_names)
    df.columns = [pretty_field_names[col] for col in df.columns]

    # Merge to get one column per chemical for the relevant columns
    # Columns of interest
    on = list(df.columns)
    on.remove('Chemical')
    on.remove('Chemical_id')
    on.remove('Supplement')
    on.remove('Concentration')

    chemicals = df.Chemical.unique()
    # If no chemicals we are done...
    if len(chemicals)==0:
        end = time.time()
        print('get_measurements took ', end-start, flush=True)
        return df

    # Do recursive join over all chemicals
    merge = df[df.Chemical==chemicals[0]]
    for i in range(1, len(chemicals)):
        to_merge = df[df.Chemical==chemicals[i]]
        merge = merge.merge(to_merge, on=on, suffixes=['', str(i+1)])

    # Original supplement becomes Supplement1 etc.
    merge = merge.rename(columns={
        'Supplement': 'Supplement1',
        'Concentration': 'Concentration1',
        'Chemical': 'Chemical1',
        'Chemical_id': 'Chemical_id1',
    })

    # Create a new Supplement and Chemical column combining the individual names
    merge['Supplement'] = merge.Supplement1
    merge['Chemical'] = merge.Chemical1
    for i in range(1, len(chemicals)):
        merge['Supplement'] += ' + ' + merge[f'Supplement{i+1}']
        merge['Chemical'] += ' + ' + merge[f'Chemical{i+1}']

    # Merge chemical ids into lists    
    merge['Chemical_id'] = merge[[f'Chemical_id{c+1}' for c in range(len(chemicals))]].values.tolist()

    end = time.time()
    print('get_measurements took ', end-start, flush=True)
    return merge

def get_biomass(df, biomass_signal):
    samp_ids = df.Sample.unique()
    m = Measurement.objects.filter(sample__id__in=samp_ids)
    m = m.filter(signal__id__exact=biomass_signal)
    biomass_df = read_frame(m, fieldnames=field_names)
    biomass_df.columns = [pretty_field_names[col] for col in biomass_df.columns]
    return biomass_df