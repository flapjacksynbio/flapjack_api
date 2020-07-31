import numpy as np
from registry.models import *
from registry.util import *
import plotly.graph_objects as go
import plotly
from plotly.colors import DEFAULT_PLOTLY_COLORS
import wellfare as wf
import time

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

def make_traces(
        fig,
        df, 
        color='blue', 
        mean=False, 
        std=False, 
        normalize=False,
        show_legend_group=False,
        group_name='',
        row=1, col=1
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

        scatter1 = go.Scatter(x=st, y=meanval, 
                                mode='lines',
                                line_color=color,
                                line=dict(width=4),
                                legendgroup=group_name,
                                name=group_name,
                                showlegend=show_legend_group)
        fig.add_trace(scatter1, row=row, col=col)

        if std:
            x = np.append(st, st[::-1])
            ylower = (meanval-stdval)[::-1]
            yupper = (meanval+stdval)
            y = np.append(yupper, ylower)
            scatter2 = go.Scatter(x=x, y=y, 
                                    mode='lines',
                                    fill='toself',
                                    line_color=color,
                                    legendgroup=group_name + 'std',
                                    name='+/- std',
                                    showlegend=show_legend_group)
            fig.add_trace(scatter2, row=row, col=col)
    else:
        scatter = go.Scattergl(x=df[xname], y=df[yname], 
                                mode='markers',
                                marker_color=color,
                                marker_size=6,
                                legendgroup=name,
                                name=name,
                                showlegend=show_legend_group)
        fig.add_trace(scatter, row=row, col=col)
    return(fig)

