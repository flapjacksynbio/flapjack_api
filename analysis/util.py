import numpy as np
import pandas as pd

# Model functions for fitting to data
# -----------------------------------------------------------------------------------
def exponential_growth(t, y0, k):
    od = y0*np.exp(k*t)
    return(od)

def exponential_growth_rate(t, y0, k):
    return(k)

def gompertz(t, y0, ymax, um, l):
    A = np.log(ymax/y0)
    log_rel_od = (A*np.exp(-np.exp((((um*np.exp(1))/A)*(l-t))+1)))
    od = y0 * np.exp(log_rel_od)
    return(od)

def gompertz_growth_rate(t, y0, ymax, um, l):
    A = np.log(ymax/y0)
    gr = um *np.exp((np.exp(1)* um *(l - t))/A - \
            np.exp((np.exp(1)* um *(l - t))/A + 1) + 2)
    return(gr)

def normalize_min_max(data, column):    
    val = data[column].values
    nval = (val-np.nanmin(val)) / (np.nanmax(val) - np.nanmin(val))
    data[column] = nval
    return data

def normalize_mean_std(data, column):    
    val = data[column].values
    nval = (val-np.nanmean(val)) / np.nanstd(val)
    data[column] = nval
    return data

def normalize_temporal_mean(data, column):    
    val = data[column].values
    t = data['Time'].values
    sval = wf.curves.Curve(x=t, y=val)
    sval = sval.normalized()
    nval = sval(t)
    data[column] = nval
    return data

def normalize_data(df, norm_type, column):
    norm_funcs = {
        'Min/Max': normalize_min_max,
        'Mean/Std': normalize_mean_std,
        'Temporal Mean': normalize_temporal_mean
    }
    norm_func = norm_funcs.get(norm_type, None)
    rows = []
    result = pd.DataFrame()
    if norm_func:
        grouped_samp = df.groupby('Sample')
        for samp_id,samp_data in grouped_samp:
            grouped_name = samp_data.groupby('Signal_id')
            for name,meas in grouped_name:
                meas = norm_func(meas, column)
                rows.append(meas)
        if len(rows)>0:
            result = result.append(rows)
        return result
    else:
        return df