import math
import json
import os
import numpy as np
from registry.models import *
from analysis import analysis
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly
from plotly.colors import DEFAULT_PLOTLY_COLORS
import wellfare as wf
import time
from django_pandas.io import read_frame

# Set of colors to use for plot markers/lines
#palette = DEFAULT_PLOTLY_COLORS
palette = [
    '#1f77b4',  # muted blue
    '#ff7f0e',  # safety orange
    '#2ca02c',  # cooked asparagus green
    '#d62728',  # brick red
    '#9467bd',  # muted purple
    '#8c564b',  # chestnut brown
    '#e377c2',  # raspberry yogurt pink
    '#7f7f7f',  # middle gray
    '#bcbd22',  # curry yellow-green
    '#17becf',   # blue-teal
    '#000000',
    '#ff0000'
]
ncolors = len(palette)

group_fields = {
    'DNA': 'sample__dna__id',
    'Study': 'sample__assay__study__id',
    'Name': 'signal__id',
    'Assay': 'sample__assay__id',
    'Media': 'sample__media__id', 
    'Strain': 'sample__strain__id', 
    'Inducer': 'sample__inducer__id'
}

def get_samples(filter):
    print('get_samples', flush=True)
    start = time.time()
    print(f"filter: {filter}", flush=True)
    studies = filter.get('studyIds')
    assays = filter.get('assayIds')
    dnas = filter.get('dnaIds')
    meds = filter.get('mediaIds')
    strains = filter.get('strainIds')
    inducers = filter.get('inducerIds')
    print(f"in get_samples inducers: {inducers}", flush=True)

    s = Sample.objects.all()
    filter_exist = False

    if studies:
        s = s.filter(assay__study__id__in=studies)
        filter_exist = True    
    if assays:
        s = s.filter(assay__id__in=assays)
        filter_exist = True    
    if dnas:
        s = s.filter(dna__id__in=dnas)
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
                                    'sample__dna__id', \
                                    'sample__inducer__id', \
                                    'sample__inducer__concentrations', \
                                    'sample__row', 'sample__col'])
    end = time.time()
    print('get_measurements took ', end-start, flush=True)
    return df
    
def make_traces(
        df, 
        color='blue', 
        mean=False, 
        std=False, 
        normalize=False,
        show_legend_group=False,
        xaxis='x1', yaxis='y1'
    ):
    '''
    Generate trace data for each sample, or mean and std, for the data in df
    '''
    df = df.sort_values('time')
    if len(df)==0:
        return(None)
    traces = []

    if mean:
        grouped_samp = df.groupby('sample__id')
        st = np.arange(df['time'].min(), df['time'].max(), 0.1)
        vals = []
        for id,samp_data in grouped_samp:
            samp_data = samp_data.sort_values('time')
            t = samp_data['time'].values
            val = samp_data['value'].values
            sval = wf.curves.Curve(x=t, y=val)
            vals.append(sval(st))
        vals = np.array(vals)
        meanval = np.nanmean(vals, axis=0)
        stdval = np.nanstd(vals, axis=0)
        traces.append({
            'x': list(st),
            'y': list(meanval),
            'marker': {'color': color},
            'type': 'scatter',
            'mode': 'lines',
            'xaxis': xaxis,
            'yaxis': yaxis
        })

        if std:
            x = np.append(st, st[::-1])
            ylower = (meanval-stdval)[::-1]
            yupper = (meanval+stdval)
            y = np.append(yupper, ylower)
            traces.append({
                'x': list(x),
                'y': list(y),
                'marker': {'color': color},
                'type': 'scatter',
                'mode': 'lines',
                'xaxis': xaxis,
                'yaxis': yaxis,
                'fill': 'toself'
            })
    else:
        traces.append({
            'x': list(df['time'].values),
            'y': list(df['value'].values),
            'marker': {'color': color},
            'type': 'scatter',
            'mode': 'markers',
            'xaxis': xaxis,
            'yaxis': yaxis,
        })
    return(traces)




def plot(df, mean=False, std=False, normalize=False, groupby1=None, groupby2=None):
    '''
        Generate plot data for frontend plotly plot generation
    '''
    if len(df)==0:
        return None

    traces = []
    axis = 1
    colors = {}
    colidx = 0
    groupby1 = group_fields[groupby1]
    groupby2 = group_fields[groupby2]
    grouped = df.groupby(groupby1)     
    n_subplots = len(grouped)   
    for name1,g1 in grouped:
        for name2,g2 in g1.groupby(groupby2):
            if name2 not in colors:
                colors[name2] = palette[colidx%ncolors]
                colidx += 1
                show_legend_group = True
            else:
                show_legend_group = False

            traces += make_traces(
                    g2,
                    color=colors[name2], 
                    mean=mean, 
                    std=std, 
                    normalize=False,
                    show_legend_group=show_legend_group,
                    xaxis='x%d'%axis, yaxis='y%d'%axis 
                )  
        axis += 1
    return traces, n_subplots

