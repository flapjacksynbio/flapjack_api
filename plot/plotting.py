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

special_case_grids = {
    3: (1,3),
    5: (2,3)    
}

def optimal_grid(n):
    '''
    Compute optimal grid of subplots for n plots
    '''
    # Special cases
    if n in special_case_grids:
        return special_case_grids[n]

    n_sqrtf = np.sqrt(n)
    n_sqrt = int(np.ceil(n_sqrtf))

    if n_sqrtf == n_sqrt:
        # Perfect square, we're done
        x, y = n_sqrt, n_sqrt
    elif n <= n_sqrt * (n_sqrt - 1):
        # An n_sqrt x n_sqrt - 1 grid is close enough to look pretty
        # square, so if n is less than that value, will use that rather
        # than jumping all the way to a square grid.
        x, y = n_sqrt, n_sqrt - 1
    elif not (n_sqrt % 2) and n % 2:
        # If the square root is even and the number of axes is odd, in
        # order to keep the arrangement horizontally symmetrical, using a
        # grid of size (n_sqrt + 1 x n_sqrt - 1) looks best and guarantees
        # symmetry.
        x, y = (n_sqrt + 1, n_sqrt - 1)
    else:
        # It's not a perfect square, but a square grid is best
        x, y = n_sqrt, n_sqrt
    return x,y

def layout_screen(fig, font_size=10):
    '''
    Layout figure optimized for screen display

    fig = figure to layout
    font_size = font size in pts

    Returns:
    fig = figure with correct layout
    '''

    fig.update_layout(  autosize=True,
                        margin=go.layout.Margin(
                            l=50,
                            r=50,
                            b=50,
                            t=50,
                            pad=0
                        ),
                        paper_bgcolor="rgb(255,255,255)",
                        template='plotly',
                        font_size=font_size
                    )
    for a in fig['layout']['annotations']:
        a['font'] = dict(size=font_size)
    fig.update_traces(marker=dict(size=6), line=dict(width=1), selector=dict(type='scatter'))
    fig.update_traces(marker=dict(size=6), line=dict(width=1), selector=dict(type='line'))
    fig.update_traces(line=dict(width=0), selector=dict(fill="toself"))
    fig.update_yaxes(linewidth=1, 
                    tickwidth=1, 
                    title_font=dict(size=font_size), 
                    tickfont=dict(size=font_size),
                    hoverformat=".2e"
                    )
    fig.update_xaxes(linewidth=1, 
                    tickwidth=1, 
                    title_font=dict(size=font_size), 
                    tickfont=dict(size=font_size),
                    hoverformat=".2e"
                    )
    return fig

def format_axes(fig, row, col, rows, xlabel='Time', ylabel='Measurement', font_size=10):
    # Format axes
    if row==rows:
        fig.update_xaxes(title_text=xlabel, 
                        title_font=dict(size=font_size), 
                        tickfont=dict(size=font_size),
                        tickwidth=3,
                        linewidth=3,
                        row=row, col=col)
    if col==1:
        fig.update_yaxes(title_text=ylabel, 
                        title_font=dict(size=font_size), 
                        tickfont=dict(size=font_size), 
                        #tickformat='.2g',
                        tickwidth=3,
                        linewidth=3,
                        row=row, col=col)
    elif col>1:
        fig.update_yaxes(title_font=dict(size=font_size), 
                        tickfont=dict(size=font_size), 
                        tickwidth=3,
                        #tickformat='.2g',
                        linewidth=3,
                        row=row, col=col)

def make_bar_traces(
        fig,
        df, 
        color='blue', 
        mean=False, 
        std=False, 
        normalize=False,
        show_legend_group=False,
        group_name='',
        row=1, col=1,
        xlabel='Vector',
        ylabel='Measurement'
    ): 
    x = df[xlabel]
    y = [df[ylabel].mean()]
    error_y = [df[ylabel].std()]
    bar = go.Bar(x=x, y=y,
                            error_y=dict(
                                        type='data', # value of error bar given in data coordinates
                                        array=error_y,
                                        visible=True),
                            marker=dict(color=color),
                            legendgroup=group_name,
                            name=group_name,
                            showlegend=show_legend_group)
    fig.add_trace(bar, row=row, col=col)
    return fig

def make_timeseries_traces(
        fig,
        df, 
        color='blue', 
        mean=False, 
        std=False, 
        normalize=False,
        show_legend_group=False,
        group_name='',
        row=1, col=1,
        xlabel='Time',
        ylabel='Measurement'
    ):
    '''
    Generate trace data for each sample, or mean and std, for the data in df
    '''
    df = df.sort_values('Time')
    if len(df)==0:
        return(None)
    traces = []

    if mean:
        grouped_samp = df.groupby('Sample')
        st = np.arange(df['Time'].min(), df['Time'].max(), 0.1)
        vals = []
        for id,samp_data in grouped_samp:
            samp_data = samp_data.sort_values('Time')
            t = samp_data['Time'].values
            val = samp_data[ylabel].values
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
                                    showlegend=False)
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

