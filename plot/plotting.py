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


def layout_screen(fig, width=800, height=500, font_size=10):
    '''
    Layout figure optimized for screen display

    fig = figure to layout
    width,height = pixel size
    font_size = font size in pts

    Returns:
    fig = figure with correct layout
    '''

    fig.update_layout(  autosize=False,
                        width=width, height=height,
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

def layout_print(fig, width=3.3, aspect=1.5, font_size=6):
    '''
    Layout figure optimized for print at 300dpi

    fig = figure to layout
    width,height = size in inches
    font_size = font size in pts

    Returns:
    fig = figure with correct layout
    '''
        
    width = width*300
    height = width/aspect
    font_size = font_size * 300/72
    fig.update_layout(  autosize=False,
                        width=width, height=height,
                        margin=go.layout.Margin(
                            l=50,
                            r=50,
                            b=50,
                            t=50,
                            pad=0
                        ),
                        paper_bgcolor="rgb(255,255,255)",
                        template='simple_white',
                        font_size=font_size
                    )
    for a in fig['layout']['annotations']:
        a['font'] = dict(size=font_size)
    fig.update_traces(marker=dict(size=6), line=dict(width=4), selector=dict(type='scatter'))
    fig.update_traces(marker=dict(size=6), line=dict(width=4), selector=dict(type='line'))
    fig.update_traces(line=dict(width=0), selector=dict(fill="toself"))
    fig.update_yaxes(linewidth=3, 
                    tickwidth=3, 
                    title_font=dict(size=font_size), 
                    tickfont=dict(size=font_size))
    fig.update_xaxes(linewidth=3, 
                    tickwidth=3, 
                    title_font=dict(size=font_size), 
                    tickfont=dict(size=font_size))
    return fig


def plot_heatmap(df, **kwargs):
    '''
    Arguments:
        fig = plotly figure
        func = function to apply to dataframe to compute curve, takes kwargs and returns a scalar
        row, col = subplot position 
        name = name of legend group
        inducer_name = name of inducer over which to compute response curve
        averaging = bool, if true plot mean and std of data, currently not used
        normalize = bool, if true normalize data to max, currently not used
        show_legend_group = bool, if true show legend entry
    '''
    
    # Get arguments or set defaults
    xname = kwargs.get('xname', 'x')
    yname = kwargs.get('yname', 'y')
    fig = kwargs.get('fig', None)
    func = kwargs.get('func', None)
    row, col = kwargs.get('row', 1), kwargs.get('col', 1)
    name = kwargs.get('name', 'data')
    show_legend_group = kwargs.get('show_legend_group', False)

    if not fig or not func:
        print('plot_kymograph: must supply a figure and a function to apply to data.')
        return
    
    print('Plotting ', name, flush=True)

    # Compute induction curve from data
    kymo,bins1,bins2 = analysis.heatmap(df, **kwargs)
    print('bins ', bins1, bins2, flush=True)
    heatmap = go.Heatmap(x=bins2, y=bins1, z=kymo, 
                        showscale=show_legend_group,
                        colorscale='Viridis')
    fig.add_trace(heatmap, row=row, col=col)

def plot_kymograph(df, **kwargs):
    '''
    Arguments:
        fig = plotly figure
        func = function to apply to dataframe to compute curve, takes kwargs and returns a scalar
        row, col = subplot position 
        name = name of legend group
        inducer_name = name of inducer over which to compute response curve
        averaging = bool, if true plot mean and std of data, currently not used
        normalize = bool, if true normalize data to max, currently not used
        show_legend_group = bool, if true show legend entry
    '''
    
    # Get arguments or set defaults
    xname = kwargs.get('xname', 'x')
    yname = kwargs.get('yname', 'y')
    fig = kwargs.get('fig', None)
    func = kwargs.get('func', None)
    row, col = kwargs.get('row', 1), kwargs.get('col', 1)
    name = kwargs.get('name', 'data')
    show_legend_group = kwargs.get('show_legend_group', False)

    if not fig:
        print('plot_kymograph: must supply a figure.')
        return
    
    print('Plotting ', name, flush=True)

    # Compute induction curve from data
    kymo,bins1,bins2 = analysis.kymograph(df, **kwargs)
    #print('bins ', bins1, bins2, flush=True)
    print('kymo', kymo, flush=True)
    heatmap = go.Heatmap(x=bins2, y=bins1, z=kymo, 
                        showscale=show_legend_group,
                        colorscale='Viridis',
                        zmin=0.)
    fig.add_trace(heatmap, row=row, col=col)
    fig.update_yaxes(autorange='reversed')
    
def plot_induction_curve(df, **kwargs):
    print(f"len(df) plotting.plot_induction_curve: {len(df)}", flush=True)
    '''
    Arguments:
        fig = plotly figure
        func = function to apply to dataframe to compute curve, takes kwargs and returns a scalar
        row, col = subplot position 
        name = name of legend group
        inducer_name = name of inducer over which to compute response curve
        color = string color in css format
        averaging = bool, if true plot mean and std of data, currently not used
        normalize = bool, if true normalize data to max, currently not used
        show_legend_group = bool, if true show legend entry
    '''
    
    # Get arguments or set defaults
    xname = kwargs.get('xname', 'x')
    yname = kwargs.get('yname', 'y')
    fig = kwargs.get('fig', None)
    func = kwargs.get('func', None)
    row, col = kwargs.get('row', 1), kwargs.get('col', 1)
    name = kwargs.get('name', 'data')
    color = kwargs.get('color', 'rgb(0,0,0)')
    show_legend_group = kwargs.get('show_legend_group', False)

    #if not fig or not func:
    #    print('plot_induction_curve: must supply a figure and a function to apply to data.')
    #    return
    
    print('Plotting ', name, flush=True)

    # Compute induction curve from data
    induction_curve = analysis.induction_curve(df, **kwargs)
    # Compute Hill function data for plotting
    ind = analysis.get_ind_hill(induction_curve)
    if ind:
        ind_hill_x, ind_hill_y, params = ind
    else:
        print('Hill function fitting failed')
        
    npts = len(df)
    marker = dict(size=4, color=color)
    xx = induction_curve[xname].values
    x = xx[xx>0.]
    y = induction_curve[yname].values
    y = y[xx>0.]
    
    print('induction_curve ', induction_curve, flush=True)
    print('xx y ', xx, y, flush=True)
    scatter1 = go.Scatter(x=np.log10(x), y=y, 
                            mode='markers',
                            marker=marker,
                            marker_size=6,
                            legendgroup=name,
                            name=name,
                            showlegend=show_legend_group)
    fig.add_trace(scatter1, row=row, col=col)
    if ind:
        scatter2 = go.Scatter(x=np.log10(ind_hill_x), y=ind_hill_y,
                                    mode='lines',
                                    line_color=color,
                                    line=dict(width=4),
                                    name='Hill function',
                                    legendgroup=name+' Hill function',
                                    showlegend=show_legend_group)
        fig.add_trace(scatter2, row=row, col=col)
    
def plot_data(df, **kwargs):
    '''
    Plot data in dataframe df, formatting according to params

    Arguments:
        xname, yname = names of columns for axes
        fig = plotly figure
        func = function to apply to dataframe to get plot data
        row, col = subplot position 
        name = name of legend group
        color = string color in css format
        averaging = 'all', 'mean', 'mean_std' - plot all data points or mean and/or std of data
        show_legend_group = bool, if true show legend entry
    '''
    
    # Get arguments or set defaults
    xname = kwargs.get('xname', 'x')
    yname = kwargs.get('yname', 'y')
    fig = kwargs.get('fig', None)
    func = kwargs.get('func', None)
    row, col = kwargs.get('row', 1), kwargs.get('col', 1)
    name = kwargs.get('name', 'data')
    color = kwargs.get('color', 'rgb(0,0,0)')
    print('color ', color, flush=True)
    averaging = kwargs.get('averaging', 'none')
    normalize = kwargs.get('normalize', 'none')
    show_legend_group = kwargs.get('show_legend_group', False)

    df = df.sort_values('time')

    #df = df.sort_values('time')
    # Process dataframe to get plot data
    if func:
        df = func(df, **kwargs)
    if len(df)==0:
        print('Empty dataframe passed to plot_data', flush=True)
        return(False)

    if 'mean' in averaging:
        grouped_samp = df.groupby('sample__id')
        st = np.arange(df['time'].min(), df['time'].max(), 0.1)
        vals = []
        for id,samp_data in grouped_samp:
            samp_data = samp_data.sort_values('time')
            t = samp_data[xname].values
            val = samp_data[yname].values
            #sval = interp1d(t, val, bounds_error=False) #, s=0, k=1)
            sval = wf.curves.Curve(x=t, y=val)
            vals.append(sval(st))
        vals = np.array(vals)
        mean = np.nanmean(vals, axis=0)
        std = np.nanstd(vals, axis=0)
        #mean,std = wf.curves.Curve.mean_std(vals, x=None)
        #mean = mean.y
        #std = std.y
        scatter1 = go.Scatter(x=st, y=mean, 
                                mode='lines',
                                line_color=color,
                                line=dict(width=4),
                                legendgroup=name,
                                name=name,
                                showlegend=show_legend_group)
        fig.add_trace(scatter1, row=row, col=col)
        if 'std' in averaging:
            x = np.append(st, st[::-1])
            ylower = (mean-std)[::-1]
            yupper = (mean+std)
            y = np.append(yupper, ylower)
            scatter2 = go.Scatter(x=x, y=y, 
                                    mode='lines',
                                    fill='toself',
                                    line_color=color,
                                    legendgroup=name + 'std',
                                    name='+/- std',
                                    showlegend=show_legend_group)
            fig.add_trace(scatter2, row=row, col=col)
    else:
        npts = len(df)
        #marker = dict(size=4, color=[color]*npts)
        scatter = go.Scattergl(x=df[xname], y=df[yname], 
                                mode='markers',
                                marker_color=color,
                                marker_size=6,
                                legendgroup=name,
                                name=name,
                                showlegend=show_legend_group)
        fig.add_trace(scatter, row=row, col=col)
    return(True)

def plot_bar(df, **kwargs): 
    '''
    Plot data in dataframe df, formatting according to params

    Arguments:
        xname, yname = names of columns for axes
        fig = plotly figure
        func = function to apply to dataframe to get plot data
        row, col = subplot position 
        name = name of legend group
        color = string color in css format
        averaging = bool, if true plot mean and std of data
        show_legend_group = bool, if true show legend entry
    '''
    
    # Get arguments or set defaults
    xname = kwargs.get('xname', 'x')
    yname = kwargs.get('yname', 'y')
    fig = kwargs.get('fig', None)
    func = kwargs.get('func', None)
    row, col = kwargs.get('row', 1), kwargs.get('col', 1)
    name = kwargs.get('name', 'data')
    color = kwargs.get('color', 'rgb(0,0,0)')
    print('color ', color, flush=True)
    averaging = kwargs.get('averaging', 'none')
    normalize = kwargs.get('normalize', 'off')
    show_legend_group = kwargs.get('show_legend_group', False)

    # Process dataframe to get plot data
    if func:
        df = func(df, **kwargs)
    if len(df)==0:
        return(False)
    x = df[xname]
    y = [df['value'].mean()]
    error_y = [df['value'].std()]
    bar = go.Bar(x=x, y=y,
                            error_y=dict(
                                        type='data', # value of error bar given in data coordinates
                                        array=error_y,
                                        visible=True),
                            marker=dict(color=color),
                            legendgroup=name,
                            name=name,
                            showlegend=show_legend_group)
    fig.add_trace(bar, row=row, col=col)
    return(True)


# DONT FORGET TO ADD @shared_task to front_view_plot_sns when changed back to front_view_plot
def plot(df, plot_func, groupby1, groupby2, groupby3, **kwargs):
    '''
        plot_func = function to apply to dataframe to generate traces

    Keyword arguments:
        xlabel,ylabel = names for axes
        Other keyword arguments are passed to the plotting function
    '''
    start = time.time()
    # current_task.update_state(state=0.1)

    # Get keyword arguments
    xlabel = kwargs.get('xlabel', 'x')
    ylabel = kwargs.get('ylabel', 'y')
    density_name = kwargs.get('density_name', None)
    ref_name = kwargs.get('ref_name', None)

    # Scale font size for 300DPI image, not 96DPI
    font_size = 300 / 96 * float(kwargs.get('font_size', 4.5))
    # Get a dataframe of the density (OD) measurements
    if density_name:
        density_df = df[df['name']==density_name]
        kwargs['density_df'] = density_df
    if ref_name:
        ref_df = df[df['name']==ref_name]
        kwargs['ref_df'] = ref_df

    normalize = kwargs.get('normalize', 'none')
    print('normalize ', normalize, flush=True)
    if normalize!='none':
        print('normalizing', flush=True)
        print('normalize', normalize, flush=True)
        df = analysis.normalize_data(df, normalize)

    # Plotting function is required
    if not plot_func:
        print('front_view_plot: must supply a plotting function')
        return(json.dumps(''))

    if len(df)==0:
        return(df)
    # Copy dataframe so we can change columns
    dfc = df.copy(deep=True)

    # Convert list columns to strings
    start2 = time.time()
    print(dfc.columns, flush=True)
    dfc['sample__dna__names'] = [' + '.join(d) for d in dfc['sample__dna__names']]
    inds = dfc['sample__inducer__names']
    # Keep the array of inducers so that we can use them in the plots
    dfc['sample__inducer__names_array'] = inds.values
    concs = dfc['sample__inducer__concentrations']
    indnames = [' + '.join(['%s (%0.2e)'%(ii,cc) for ii,cc in zip(i,c)]) for i,c in zip(inds,concs)]
    dfc['sample__inducer__names'] = indnames
    end2 = time.time()
    print('Converting array columns took ', end2-start2, flush=True)

    # current_task.update_state(state=0.3)
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
    print('ncolors ', ncolors, flush=True)
    html = {}
    for name1,g1 in dfc.groupby(groupby1):
        grouped = g1.groupby(groupby2)
        n_sub_plots = len(grouped)
        if n_sub_plots>3:
            rows = int(np.ceil(np.sqrt(n_sub_plots)))
            cols = int(np.ceil(n_sub_plots/rows))
            cols = max(cols,1)
        else:
            rows = 1
            cols = n_sub_plots

        figure_width = 999
        figure_height = rows * 999 / (cols+1)
        fig = make_subplots(
                            rows=rows, cols=cols,
                            subplot_titles=[name for name,g in grouped],
                            shared_xaxes=True, shared_yaxes=False,
                            vertical_spacing=0.1, horizontal_spacing=0.1
                            )        
        #fig = plt.figure(figsize=(7,7))
        
        colors = {}
        colidx = 0
        i=0
        # current_task.update_state(state=0.5)
        for name2,g2 in grouped:
            for name3,g3 in g2.groupby(groupby3):
                if name3 not in colors:
                    colors[name3] = palette[colidx%ncolors]
                    colidx += 1
                    show_legend_group = True
                else:
                    show_legend_group = False

                row=1+i//cols
                col=1+i%cols

                kwargs['fig'] = fig
                kwargs['row'] = row
                kwargs['col'] = col
                kwargs['color'] = colors[name3]
                kwargs['show_legend_group'] = show_legend_group
                kwargs['name'] = name3

                # Apply the plot function to add traces to figure
                #plt.subplot(rows,cols,i+1)
                #plt.plot(g3['time'], g3['value'], '.')
                print('plot_func ', plot_func, flush=True)
                plot_func(g3, **kwargs)
                
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
            i += 1        
        fig.update_layout(
                            autosize=False,
                            width=figure_width, height=figure_height,
                            margin=go.layout.Margin(
                                l=50,
                                r=50,
                                b=50,
                                t=50,
                                pad=0
                            ),
                            #yaxis = dict(
                            #    showexponent = 'all',
                            #    exponentformat = 'e'
                            #),
                            #yaxis_tickformat = '~e.2',
                            paper_bgcolor="rgb(255,255,255)",
                            template='simple_white',
                            font_size=font_size,
                            hoverlabel=dict(font=dict(size=font_size)),
                            #title=name1
                        )
        for a in fig['layout']['annotations']:
            a['font'] = dict(size=font_size)
        #fig_html = plotly.io.to_html(fig, \
        #                    include_plotlyjs=False, \
        #                    full_html=False, \
        #                    )
        html[name1] = fig #fig_html
    # current_task.update_state(state=0.8)
    end = time.time()
    print('Done plotting, time elapsed ', end-start, flush=True)
    # current_task.update_state(state=0.98)
    return(html) #json.dumps(html))

