import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from django_pandas.io import read_frame
from registry.models import *
from registry.util import *
from scipy.interpolate import interp1d, UnivariateSpline
from scipy.signal import medfilt, savgol_filter
import wellfare as wf
import time



def normalize_min_max(data):    
    val = data['value'].values
    nval = (val-np.nanmin(val)) / (np.nanmax(val) - np.nanmin(val))
    data = data.assign(value=nval)
    return data

def normalize_mean_std(data):    
    val = data['value'].values
    nval = (val-np.nanmean(val)) / np.nanstd(val)
    data = data.assign(value=nval)
    return data

def normalize_temporal_mean(data):    
    val = data['value'].values
    t = data['time'].values
    sval = wf.curves.Curve(x=t, y=val)
    sval = sval.normalized()
    nval = sval(t)
    data = data.assign(value=nval)
    return data

def normalize_data(df, norm_type):
    norm_funcs = {
        'min_max': normalize_min_max,
        'mean_std': normalize_mean_std,
        'temporal_mean': normalize_temporal_mean
    }
    norm_func = norm_funcs.get(norm_type, None)
    rows = []
    result = pd.DataFrame()
    if norm_func:
        grouped_samp = df.groupby('sample__id')
        for samp_id,samp_data in grouped_samp:
            grouped_name = samp_data.groupby('name')
            for name,meas in grouped_name:
                meas = norm_func(meas)
                rows.append(meas)
        if len(rows)>0:
            result = result.append(rows)
        return result
    else:
        return df

def compute_background(assay, media, strain):
    s = Sample.objects.filter(assay__name__exact=assay) \
                        .filter(media__name__exact=media)
    samps_no_cells = s.filter(vector__dnas__name__exact='none').filter(strain__name__exact='None')
    samps_no_dna = s.filter(vector__dnas__name__exact='none').filter(strain__name__exact=strain)
    meas_no_cells = get_measurements(samps_no_cells)
    meas_no_dna = get_measurements(samps_no_dna)

    # Compute media background
    bg_media = {}
    grouped_meas = meas_no_cells.groupby('Signal')
    for name,data_meas in grouped_meas:
        vals = []
        grouped_samp = data_meas.groupby('Sample')
        for samp_id,data_samp in grouped_samp:
            data_samp = data_samp.sort_values('Time')
            vals.append(data_samp['Measurement'].values)
        vals = np.array(vals)
        bg_media[name] = (np.mean(vals, axis=0), np.std(vals, axis=0))

    # Compute strain background
    bg_strain = {}
    grouped_meas = meas_no_dna.groupby('Signal')
    for name,data_meas in grouped_meas:
        vals = []
        grouped_samp = data_meas.groupby('Sample')
        for samp_id,data_samp in grouped_samp:
            data_samp = data_samp.sort_values('Time')
            vals.append(data_samp['Measurement'].values)
        vals = np.array(vals)
        bg_strain[name] = (np.mean(vals, axis=0), np.std(vals, axis=0))

    return bg_media,bg_strain

def get_bg_corrected(samples, density_name, bg_std_devs=2., min_density=0.05, remove_data=False, signals=None):
    bg_all = {}

    # Empty dataframe to accumulate result
    meas_bg_corrected = pd.DataFrame()

    # Ignore background samples
    meas = get_measurements(samples.exclude(vector__dnas__name__exact='none'), signals)
    # Loop over samples
    rows = []
    grouped_sample = meas.groupby('Sample')
    for samp_id,sample_data in grouped_sample:
        assay = sample_data['Assay'].values[0]
        media = sample_data['Media'].values[0]
        strain = sample_data['Strain'].values[0]
        key = (assay,media,strain)
        if key not in bg_all:
            bg_media,bg_strain = compute_background(assay, media, strain)
            #print('Computed background for ', key, bg_media, bg_strain)
            bg_all[key] = bg_media, bg_strain
        else:
            bg_media, bg_strain = bg_all[key]
        grouped_name = sample_data.groupby('Signal')   
        # Loop over measurement names
        for name,meas_data in grouped_name:
            meas_data = meas_data.sort_values('Time')
            time = meas_data['Time']
            vals = meas_data['Measurement'].values
            if name==density_name:
                # Correct OD
                bg_media_mean, bg_media_std = bg_media.get(name, (0.,0.))
                vals_corrected = vals - bg_media_mean
                if remove_data:
                    print('Correcting OD bg', flush=True)
                    print('Removing %d data points'%np.sum(vals_corrected < bg_std_devs*bg_media_std), flush=True)
                    vals_corrected[vals_corrected < np.maximum(bg_std_devs*bg_media_std, min_density)] = np.nan
                #print('bgmean, bgstd = ', bg_media_mean, bg_media_std)
            else:
                # Correct fluorescence
                bg_strain_mean, bg_strain_std = bg_strain.get(name, (0.,0.))
                vals_corrected = vals - bg_strain_mean
                if remove_data:
                    print('Correcting fluo bg', flush=True)
                    print('Removing %d data points'%np.sum(vals_corrected < bg_std_devs*bg_strain_std), flush=True)
                    vals_corrected[vals_corrected < bg_std_devs*bg_strain_std] = np.nan
                #print('bgmean, bgstd = ', bg_strain_mean, bg_strain_std)

            # Remove all data at times earlier than the last NaN
            idx = np.where(np.isnan(vals_corrected[::-1]))[0]
            if len(idx)>0:
                # Set all data before this time to NaN
                vals_corrected[:len(vals_corrected)-idx[0]] = np.nan

            # Put values into dataframe
            #meas_data = meas_data.assign(Rate=vals_corrected)
            meas_data['Measurement'] = vals_corrected
            rows.append(meas_data)
            print('vals_correcfted ', vals_corrected, flush=True)

    if len(rows)>0:
        meas_bg_corrected = meas_bg_corrected.append(rows)        
    # Remove data meeting correction criteria
    meas_bg_corrected = meas_bg_corrected.dropna(subset=['Measurement'])
    print(meas_bg_corrected.head(), flush=True)
    return(meas_bg_corrected)

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

# Analysis functions that compute timeseries from a dataframe with given keyword args
# -----------------------------------------------------------------------------------

'''
def ratiometric_rho(df, params):
    # Parameters:
    #   df = data frame to analyse
    #   density_name = name of measurement to use for biomass or density
    rho_x = params.get('rho_x', 'CFP')
    rho_y = params.get('rho_y', 'RFP')

    result = pd.DataFrame()
    rows_to_append = []
    lowess = sm.nonparametric.lowess

    # Loop over samples
    print(f"Samples: {len(df.groupby('sample__id'))}", flush=True)
    for samp_id, data in df.groupby('sample__id'):
        data = data.sort_values('time')
        xdata = data[data['name']==rho_x]
        ydata = data[data['name']==rho_y]
        if len(xdata>21) and len(ydata>21):
            tx = xdata['time']
            x = savgol_filter(xdata['value'], 21, 3, mode='interp') 
            #medfilt(xdata['value'],11) #.rolling(window=10, min_periods=1).median()
            ty = ydata['time']
            y = savgol_filter(ydata['value'], 21, 3, mode='interp')  
            #medfilt(ydata['value'],11) #.rolling(window=10, min_periods=1).median()
            
            if(len(x) > 1 and len(tx) > 1 and len(y) > 1 and len(ty) > 1):
                ix = interp1d(tx,x)
                iy = interp1d(ty,y)

                # Compute time range
                tmin = max(tx.min(), ty.min())
                tmax = min(tx.max(), ty.max())
                t = np.linspace(tmin, tmax, 100)

                sx = ix(t) #savgol_filter(ix(t), 21, 3, mode='interp')             
                sy = iy(t) #savgol_filter(iy(t), 21, 3, mode='interp') 

                iz = interp1d(sx, sy)
                xmin = sx.min()
                xmax = sx.max()
                xx = np.linspace(xmin, xmax, 100)
                
                sz = UnivariateSpline(xx, iz(xx), s=0, k=1)
                rho = sz.derivative()(x)

                rows = data[data['name']==rho_x]
                rows = rows.assign(value=rho)
                # Reslice data to new time range
                rows = rows[ (rows.time>=tmin) & (rows.time<tmax) ]
                #print('tmin, tmax: ', tmin, tmax, flush=True)
                rows_to_append.append(rows)
    if len(rows_to_append)>0:
        result = result.append(rows)
    return(result)
'''

def velocity(df, params):
    '''
    Parameters:
       df = data frame to analyse
       pre_smoothing = Savitsky-Golay filter parameter (window size)
       post_smoothing = Savitsky-Golay filter parameter (window size)
    '''
    smoothing_type = params.get('smoothing_type', 'savgol')
    smoothing_param1 = params.get('pre_smoothing', 21)
    smoothing_param2 = params.get('post_smoothing', 21)

    print(smoothing_param1, smoothing_param2, flush=True)
    
    result = pd.DataFrame()
    rows = []

    if smoothing_type=='lowess':
        lowess = sm.nonparametric.lowess

    grouped_sample = df.groupby('Sample')
    n_samples = len(grouped_sample)
    # Loop over samples
    si = 1
    for samp_id, samp_data in grouped_sample:
        print('Computing velocity of sample %d of %d'%(si, n_samples), flush=True)
        si += 1
        for meas_name, data in samp_data.groupby('Signal'):
            data = data.sort_values('Time')
            time = data['Time'].values
            val = data['Measurement'].values
            
            if smoothing_type=='savgol':
                min_data_pts = max(smoothing_param1,smoothing_param2)
            else:
                min_data_pts = 2
            print(len(val), flush=True)
            if len(val)>min_data_pts:
                # Interpolation
                ival = interp1d(time, val)
                
                # Savitzky-Golay filter
                if smoothing_param1>0:
                    if smoothing_type=='savgol':
                        print('Applying savgol filter', flush=True)
                        sval = savgol_filter(val, int(smoothing_param1), 2, mode='interp')
                        print(len(val), flush=True)
                    elif smoothing_type=='lowess':
                        print('Applying lowess filter', flush=True)
                        z = lowess(val, time, frac=smoothing_param1)
                        sval = z[:,1]
                        print(len(val), flush=True)

                # Interpolation
                sval = interp1d(time, sval)

                # Compute expression rate for time series
                velocity = savgol_filter(ival(time), int(smoothing_param1), 2, deriv=1, mode='interp')
 
                # Final Savitzky-Golay filtering of expression rate profile
                if smoothing_param2>0:
                    if smoothing_type=='savgol':
                        velocity = savgol_filter(velocity, int(smoothing_param2), 2, mode='interp')
                    elif smoothing_type=='lowess':
                        z = lowess(velocity, time, frac=smoothing_param2)
                        ksynth = z[:,1]
                # Put result in dataframe
                data = data.assign(Measurement=velocity)
                rows.append(data)
    if len(rows)>0:
        result = result.append(rows)
    else:
       print('No rows to add to velocity dataframe', flush=True)

    return(result)

def expression_rate_indirect(df, params):
    '''
    Parameters:
       df = data frame to analyse
       density_df = dataframe with density measurements
       pre_smoothing = Savitsky-Golay filter parameter (window size)
       post_smoothing = Savitsky-Golay filter parameter (window size)
    '''
    density_name = params.get('biomass_signal')
    density_df = df[df['Signal']==density_name]
    smoothing_type = params.get('smoothing_type', 'savgol')
    smoothing_param1 = params.get('pre_smoothing', 21)
    smoothing_param2 = params.get('post_smoothing', 21)

    print(smoothing_param1, smoothing_param2, flush=True)
    
    result = pd.DataFrame()
    rows = []

    if smoothing_type=='lowess':
        lowess = sm.nonparametric.lowess

    grouped_sample = df.groupby('Sample')
    n_samples = len(grouped_sample)
    # Loop over samples
    si = 1
    for samp_id, samp_data in grouped_sample:
        print('Computing expression rate of sample %d of %d'%(si, n_samples), flush=True)
        si += 1
        for meas_name, data in samp_data.groupby('Signal'):
            data = data.sort_values('time')
            time = data['Time'].values
            val = data['Measurement'].values
            density = density_df[density_df['Sample']==samp_id]
            density = density.sort_values('Time')
            density_val = density['Measurement'].values
            density_time = density['Time'].values
            
            if smoothing_type=='savgol':
                min_data_pts = max(smoothing_param1,smoothing_param2)
            else:
                min_data_pts = 2
            print(len(val), flush=True)
            if len(val)>min_data_pts and len(density_val)>min_data_pts:
                # Interpolation
                ival = interp1d(time, val)
                idensity = interp1d(density_time, density_val)

                # Savitzky-Golay filter
                if smoothing_param1>0:
                    if smoothing_type=='savgol':
                        print('Applying savgol filter', flush=True)
                        sval = savgol_filter(val, int(smoothing_param1), 2, mode='interp')
                        sdensity = savgol_filter(density_val, int(smoothing_param1), 2, mode='interp')
                        print(len(val), len(density_val), flush=True)
                    elif smoothing_type=='lowess':
                        print('Applying lowess filter', flush=True)
                        z = lowess(val, time, frac=smoothing_param1)
                        sval = z[:,1]
                        z = lowess(density_val, density_time, frac=smoothing_param1)
                        sdensity = z[:,1]
                        print(len(val), len(density_val), flush=True)

                # Interpolation
                sval = interp1d(time, sval)
                sdensity = interp1d(density_time, sdensity)

                # Compute time range
                tmin = max(time.min(), density_time.min())
                tmax = min(time.max(), density_time.max())
                time = time[ (time>=tmin) & (time<tmax)]

                # Reslice data to new time range
                data = data[ (data.time>=tmin) & (data.time<tmax) ]

                # Compute expression rate for time series
                dvaldt = savgol_filter(ival(time), int(smoothing_param1), 2, deriv=1, mode='interp')
                ksynth = dvaldt / sdensity(time)
                #dvaldt = sval.derivative()(time)
                #ksynth = dvaldt / (sdensity(time) + 0.)

                # Compute promoter activity d/dt(I/A)
                #conc = sval(time) / sdensity(time)
                #sconc = UnivariateSpline(time, conc, s=0, k=3)
                #ksynth = sconc.derivative()(time)
 
                # Final Savitzky-Golay filtering of expression rate profile
                if smoothing_param2>0:
                    if smoothing_type=='savgol':
                        ksynth = savgol_filter(ksynth, int(smoothing_param2), 2, mode='interp')
                    elif smoothing_type=='lowess':
                        z = lowess(ksynth, time, frac=smoothing_param2)
                        ksynth = z[:,1]
                # Put result in dataframe
                data = data.assign(value=ksynth)
                rows.append(data)
    if len(rows)>0:
        result = result.append(rows)
    else:
       print('No rows to add to expression rate dataframe', flush=True)

    return(result)

def expression_rate_direct(df, params):
    '''
    Parameters:
        df = data frame to analyse
        density_df = dataframe containing density (biomass) measurements
        degr = degradation rate of reporter protein
        eps_L = insignificant value for model fitting
    '''
    density_name = params.get('density_name')
    density_df = df[df['name']==density_name]
    degr = params.get('degr', 0.)
    eps_L = params.get('eps_L', 1e-7)

    print(degr, eps_L, flush=True)
    
    result = pd.DataFrame()
    rows = []

    grouped_sample = df.groupby('sample__id')
    n_samples = len(grouped_sample)
    # Loop over samples
    si = 1
    for samp_id, samp_data in grouped_sample:
        print('Computing expression rate of sample %d of %d'%(si, n_samples), flush=True)
        si += 1
        for meas_name, data in samp_data.groupby('name'):
            data = data.sort_values('time')
            time = data['time']
            val = data['value']
            density = density_df[density_df['sample__id']==samp_id]
            density = density.sort_values('time')
            density_val = density['value']
            density_time = density['time']

            if len(val)>1:
                # Construct curves
                fpt = time.values
                fpy = val.values
                cfp = wf.curves.Curve(x=fpt, y=fpy)
                odt = density_time.values
                ody = density_val.values
                cod = wf.curves.Curve(x=odt, y=ody)
                # Compute time range
                xmin, xmax = cod.xlim()
                ttu = np.arange(xmin, xmax, 0.1)
                # Fit model
                if meas_name==density_name:
                    ksynth, _, _, _, _ = wf.infer_growth_rate(cod, ttu, 
                                                                eps_L=eps_L, 
                                                                positive=True)
                else:
                    ksynth, _, _, _, _ = wf.infer_synthesis_rate_onestep(cfp, cod, ttu, 
                                                                            degr=degr, eps_L=eps_L, 
                                                                            positive=True)
                data = data.assign(value=ksynth(fpt))
                rows.append(data)
    if len(rows)>0:
        result = result.append(rows)
    else:
        print('No rows to add to expression rate dataframe', flush=True)
    return(result.dropna())



# Analysis functions that compute value from a dataframe with given keyword args
# ----------------------------------------------------------------------------------
def ratiometric_alpha(df, params):
    # Parameters:
    #   bounds = tuple of list of min and max values for  Gompertz model parameters
    #   df = dataframe of measurements including OD
    #   density_df = dataframe containing biomass measurements
    #   ndt = number of doubling times to extend exponential phase
    density_name = params.get('density_name')
    density_df = df[df['name']==density_name]
    bounds = params['bounds']
    ndt = params['ndt']

    result = pd.DataFrame()
    rows = []

    grouped_samples = df.groupby('sample__id')
    for samp_id,data in grouped_samples:
        # input values for Gompertz model fit
        oddf = density_df[density_df['sample__id']==samp_id]
        oddf = oddf.sort_values('time')
        odt = oddf['time'].values
        odval = oddf['value'].values
        odt = odt[odval>0.]
        odval = odval[odval>0.]
        #y = np.log(odval[odval>0.]) - np.log(np.nanmin(odval[odval>0.]))

        # Fit Gompertz model
        try:
            z,_=curve_fit(gompertz, odt, odval, bounds=bounds)
        except:
            break
            
        y0 = z[0]
        ymax = z[1]
        A = np.log(ymax/y0)
        um = z[2]
        l = z[3]


        print('y0, ymax, um, l', y0, ymax, um, l, flush=True)

        # Compute time of peak growth
        tm = ((A/(np.exp(1)*um))+l)
        # Compute doubling time at peak growth
        dt = np.log(2)/um
        # Time range to consider exponential growth phase
        t1 = tm
        t2 = tm + ndt*dt

        print('t1, t2', t1, t2, flush=True)

        # Compute alpha as slope of fluo vs od for each measurement name
        grouped_name = data.groupby('name')
        for name,data in grouped_name:
            # fluorescence measurements
            mdf = data[(data['time']>=t1) & (data['time']<=t2)]
            mdf = mdf.sort_values('time')
            mval = mdf['value'].values
            mt = mdf['time'].values
            
             # od measurements
            oddf = oddf[(oddf['time']>=t1)&(oddf['time']<=t2)]
            oddf = oddf.sort_values('time')
            odval = oddf['value'].values
            odt = oddf['time'].values
            
            if len(mt)>1 and len(odt)>1:
                smval = interp1d(mt, mval, kind='linear', bounds_error=False)
                sodval = interp1d(odt, odval, kind='linear', bounds_error=False)

                tmin = max(odt.min(), mt.min())
                tmax = min(odt.max(), mt.max())
                print('tmin, tmax', tmin, tmax, flush=True)
                times = np.linspace(tmin,tmax,100)

                z = np.polyfit(sodval(times), smval(times), 1)
                p = np.poly1d(z)

                # Get slope as alpha
                alpha = z[0]

                # Get dataframe with single row containing alpha for this sample, name
                data = data.iloc[0]
                data['value'] = alpha
            else:
                data = data.iloc[0]
                data['value'] = np.nan
            # Append to list of rows to append to result
            rows.append(data)
    # Append alpha values to result df
    if len(rows)>0:
        result=result.append(rows)
    return result

def ratiometric_rho(df, params):
    # Parameters:
    #   bounds = tuple of list of min and max values for  Gompertz model parameters
    #   df = dataframe of measurements including OD
    #   density_df = dataframe containing biomass measurements
    #   ref_df = dataframe containing reference measurements
    #   ndt = number of doubling times to extend exponential phase
    density_name = params.get('density_name')
    ref_name = params.get('ref_name')
    density_df = df[df['name']==density_name]
    ref_df = df[df['name']==ref_name]
    bounds = params['bounds']
    ndt = params['ndt']

    alpha = ratiometric_alpha(df, params)
    alpha_ref = ratiometric_alpha(ref_df, params)

    alpha = alpha.sort_values('sample__id')
    alpha_ref = alpha_ref.sort_values('sample__id')

    result = pd.DataFrame()
    rows = [] 
    grouped = alpha.groupby('name')
    # Normalise each measurement separately by the reference
    for name_id,data in grouped:
        data = data.sort_values('sample__id')
        vals = data['value'].values
        ref = alpha_ref['value'].values
        data['value'] = vals / ref
        rows.append(data)
    result = result.append(rows)
    return result     



def mean_expression_ratio(df, params):
    '''
    Return a dataframe containing the ratio of mean values for each sample,name in the input dataframe df
    '''
    all_mean = mean_expression(df, params)
    ref_name = params.get('ref_name', None)
    ref_df = df[df['name']==ref_name]
    ref_df = mean_expression(ref_df)
    ref = ref_df['value'].values

    result = pd.DataFrame()
    rows = [] 
    grouped = all_mean.groupby('name')
    # Normalise each measurement separately by the reference
    for name_id,data in grouped:
        vals = data['value'].values
        data['value'] = vals / ref
        rows.append(data)
    result = result.append(rows)
    return result     


def mean_expression_rate(df, params):
    '''
    Return a dataframe containing the mean value for each sample,name in the input dataframe df
    '''
    density_name = params.get('density_name', None)
    if density_name:
        density_df = df[df['name']==density_name]
    else:
        return result
    rows = []

    # Compute mean expression rate as average of time series
    #expr = expression_rate_direct(df, density_name=density_name)
    #result = mean_expression(expr)

    # Compute mean expression rate as finite diff between start and end
    result = pd.DataFrame()
    grouped = df.groupby('sample__id')
    for samp_id,data in grouped:
        density = density_df[density_df['sample__id']==samp_id]
        density_df = density_df.sort_values('time')
        mean_density = density['value'].mean()
        for name,meas in data.groupby('name'):
            meas = meas.sort_values('time')
            df = meas['value'].values[-1] - meas['value'].values[0]
            dt = meas['time'].values[-1] - meas['time'].values[0]
            meas = meas.iloc[[0]]
            meas = meas.assign(value=df/dt/mean_density)
            rows.append(meas)
    result = result.append(rows)
    return result

def mean_expression_rate_ratio(df, params):
    '''
    Return a dataframe containing the mean value for each sample,name in the input dataframe df
    '''
    result = pd.DataFrame()
    ref_name = params.get('ref_name', None)
    if ref_name:
        ref_df = df[df['name']==ref_name]
    else:
        return result
    rows = []
    df = df.sort_values('time')
    grouped = df.groupby('sample__id')
    for samp_id,data in grouped:
        ref = ref_df[ref_df['sample__id']==samp_id]
        for name,meas in data.groupby('name'):
            df = meas['value'].values[-1] - meas['value'].values[0]
            dref = ref['value'].values[-1] - ref['value'].values[0]
            meas = meas.iloc[[0]]
            meas = meas.assign(value=df/dref)
            rows.append(meas)
    result = result.append(rows)
    return result


def mean_expression(df, params):
    '''
    Return a dataframe containing the mean value for each sample,name in the input dataframe df
    '''
    agg = {}
    for column_name in df.columns:
        if column_name!='sample__id' and column_name!='name':
            agg[column_name] = 'first'
    agg['value'] = 'mean'
    grouped_samples = df.groupby(['sample__id', 'name'], as_index=False)
    mean = grouped_samples.agg(agg)
    return mean     

def max_expression(df, params):
    '''
    Return a dataframe containing the max value for each sample,name in the input dataframe df
    '''
    agg = {}
    for column_name in df.columns:
        if column_name!='sample__id' and column_name!='name':
            agg[column_name] = 'first'
    agg['value'] = 'max'
    grouped_samples = df.groupby(['sample__id', 'name'], as_index=False)
    max_expr = grouped_samples.agg(agg)
    return max_expr    

def mean_velocity(df, params):
    '''
    Return a dataframe containing the max value for each sample,name in the input dataframe df
    '''
    df = velocity(df, params)
    agg = {}
    for column_name in df.columns:
        if column_name!='sample__id' and column_name!='name':
            agg[column_name] = 'first'
    agg['value'] = 'mean'
    grouped_samples = df.groupby(['sample__id', 'name'], as_index=False)
    mean_expr = grouped_samples.agg(agg)
    return mean_expr    

def max_velocity(df, params):
    '''
    Return a dataframe containing the max value for each sample,name in the input dataframe df
    '''
    df = velocity(df, params)
    agg = {}
    for column_name in df.columns:
        if column_name!='sample__id' and column_name!='name':
            agg[column_name] = 'first'
    agg['value'] = 'max'
    grouped_samples = df.groupby(['sample__id', 'name'], as_index=False)
    max_expr = grouped_samples.agg(agg)
    return max_expr    

def kymograph(df, params):
    '''
    Compute kymograph for induced expression, x-axis=inducer concentration
    '''
    density_name = params.get('density_name', None)
    #func = params.get('func', expression_rate_direct)
    inducer_name = params.get('inducer_name', None)

    concs = []
    times = []
    values = []

    for samp_id,samp_data in df.groupby('sample__id'):
        inducer_names = samp_data['sample__inducer__names_array'].values[0]
        inducer_concs = samp_data['sample__inducer__concentrations'].values[0]
        
        if len(inducer_names)==1:
            if inducer_name==inducer_names[0]:
                func_df = samp_data #func(samp_data, params)
                if len(func_df)>0:
                    val = func_df['value'].values
                    time = func_df['time'].values
                    values.extend(val)
                    times.extend(time)
                    concs.extend([inducer_concs[0]]*len(val))
        elif len(inducer_names)==0: 
                func_df = samp_data #func(samp_data, params)
                if len(func_df)>0:
                    val = func_df['value'].values
                    time = func_df['time'].values
                    values.extend(val)
                    times.extend(time)
                    concs.extend([0.]*len(val))

    x = np.array(times)
    y = np.array(concs)
    z = np.array(values)
    idx = np.where(y>0)

    unique_times = np.unique(x[idx])
    n_times = len(unique_times) + 2
    unique_concs = np.unique(y[idx])
    n_concs = len(unique_concs) + 2

    df = pd.DataFrame({'value':z[idx], 't':x[idx], 'conc':np.log10(y[idx])})
    if len(df)>0:
        c1,bins1 = pd.cut(df.t, bins=n_times, retbins=True)
        c2,bins2 = pd.cut(df.conc, bins=n_concs, retbins=True)       
        hm = df.groupby([c1, c2]).value.mean().unstack()

        #print('c1, c2 ', c1, c2, flush=True)
        print('bin sizes ', len(bins1), len(bins2), flush=True)
        #print('bins ', bins1, bins2, flush=True)
        print('size kymo ', hm.shape, flush=True)
        return hm,bins1,bins2
    else:
        return [0],[0],[0]

def heatmap(df, params):
    # func() takes a dataframe as argument and returns another timeseries, eg. expression rate
    func = params.get('func', mean_expression)
    xname = params.get('xname', 'xname')

    func_df = func(df, params)
    c1,bins1 = pd.cut(func_df[xname], bins=100, retbins=True)
    c2,bins2 = pd.cut(func_df[yname], bins=100, retbins=True)
    hm = func_df.groupby([c1, c2]).value.mean().unstack()

    #print('c1, c2 ', c1, c2, flush=True)
    print('bin sizes ', len(bins1), len(bins2), flush=True)
    #print('bins ', bins1, bins2, flush=True)
    print('size heatmap ', hm.shape, flush=True)
    return hm,bins1,bins2

def induction_curve(df, params):
    '''
    Arguments:
        inducer_name = name of inducer over which to compute induction curve
        func = function to apply to dataframe to get values for response curve
    '''
    # Get parameters or set defaults
    inducer_name = params.get('inducer_name', None)
    func = params.get('func', None)

    # Required arguments
    #if not inducer_name or not func:
    #    print('induction_curve: must supply name of inducer and function')
    #    return None

    concs = []
    expr = []
    grouped_samps = df.groupby('sample__id')
    for samp_id,samp in grouped_samps:
        inducer_names = samp['sample__inducer__names'].values[0]
        inducer_concs = samp['sample__inducer__concentrations'].values[0]
        if len(inducer_names)==0: 
            # func_df = func(samp, params)
            # if type(func_df) == pd.core.frame.DataFrame:
            #     concs.append(0.0)
            #     expr.append(func_df['value'].mean())
            # elif np.isnan(func_df):
            #     pass
            # else:
            #     concs.append(0.0)
            #     expr.append(func_df)
            concs.append(0.0)
            expr.append(samp['value'].mean())
        elif inducer_name in inducer_names:
            ind_idx = inducer_names.index(inducer_name)
            # func_df = func(samp, params)
            # if type(func_df) == pd.core.frame.DataFrame:
            #     concs.append(inducer_concs[ind_idx])
            #     expr.append(func_df['value'].mean())
            # elif np.isnan(func_df):            
            #     pass
            # else:
            #     concs.append(inducer_concs[ind_idx])
            #     expr.append(func_df)
            concs.append(inducer_concs[ind_idx])
            expr.append(samp['value'].mean())
    df = pd.DataFrame({'Expression':expr, 'Concentration':concs})
    return df

def induction_heatmap(qsamples, func, nbins, params):
    # Get inducer concentrations
    #concs1 = [s.inducers[0].concentration for s in qsamples]
    #concs2 = [s.inducers[1].concentration for s in qsamples]

    #FIX THIS [0] in FlapWeb is [1] in flapjack
    concs1 = [Inducer.objects.filter(sample__id__exact=s.id)[1].concentration for s in qsamples]
    concs2 = [Inducer.objects.filter(sample__id__exact=s.id)[0].concentration for s in qsamples]
    concs1 = np.array(concs1)
    concs2 = np.array(concs2)

    # Compute values
    values = []
    for s in qsamples:
        df = get_measurements(s)
        params['df'] = df
        # Apply function to measurements dataframe
        value = func(params)
        values.append(value)
    values = np.array(values)

    # Group data as heatmap array
    idx = np.where((concs1>0)*(concs2>0))[0]
    x = np.log10(concs1[idx])
    y = np.log10(concs2[idx])
    z = values[idx]
    df = pd.DataFrame({'value':z, 'conc1':x, 'conc2':y})
    c1,bins1 = pd.cut(df.conc1, nbins, retbins=True)
    c2,bins2 = pd.cut(df.conc2, nbins, retbins=True)
    hm = df.groupby([c1, c2]).value.mean().unstack()

    return hm,bins1,bins2

# Analysis functions that take a list of DNA names, and compute some measure, returning a list
# --------------------------------------------------------------------------------------------


def hill(x, a, b, k, n):
    return (a*(x/k)**n + b) / (1 + (x/k)**n)

def get_ind_hill(df):
    expression = df.columns[0]
    concs = df['Concentration']
    concs_log = np.log10(concs)
    inf_ind = np.where(concs>0.)[0]
    scale_y = df[expression].max()
    norm_y = df[expression] / scale_y
    scale_concs = concs.max()
    norm_concs = concs / scale_concs
    # Fix maxfev, put it back to 1000 (default) and catch error of not finding optimal parameters

    # Set sensible bounds for normalised values
    bounds = ([0., 0., 0., 1.], [1., 1., 1., 5.])

    try:
        z,cov = curve_fit(hill, norm_concs, norm_y, bounds=bounds, maxfev=1000)
        a,b,k,n = z
        a_std, b_std, k_std, n_std = np.sqrt(np.diag(cov))
        x = np.linspace(concs_log[inf_ind].min(),concs_log.max(),200)

        a = a*scale_y
        b = b*scale_y
        k = k*scale_concs
        a_std = a_std*scale_y
        b_std = b_std*scale_y
        k_std = k_std*scale_concs
        concs = 10**x
        val = hill(10**x, a, b, k, n)
        params = (a,b,k,n, a_std,b_std,k_std,n_std)
        return concs, val, params
    except:
        print('Hill function fit failed')
        return None

def exp_ratiometric_rho(df, params):
    '''
    Return the value of rho (dx/do/dy/do) for the sample in df
    '''
    density_name = params.get('density_name', 'OD')
    rho_x = params.get('rho_x', 'CFP')
    rho_y = params.get('rho_y', 'YFP')

    grouped_df = df.groupby('sample__id')
    result = pd.DataFrame()
    si = 0
    for samp_id, samp in grouped_df:
        si += 1
        df_d = samp[(samp['name']==density_name)]
        df_d = df_d.sort_values(by='time')
        df_x = samp[(samp['name']==rho_x)]
        df_x = df_x.sort_values(by='time')
        df_y = samp[(samp['name']==rho_y)]
        df_y = df_y.sort_values(by='time')

        d_value = df_d['value']
        d_time = df_d['time']   
        x_value = df_x['value']
        x_time = df_x['time']
        y_value = df_y['value']
        y_time = df_y['time']

        rho = np.nan
        try:
            z,_=curve_fit(gompertz, d_time, d_value, maxfev = 1000)#, bounds=bounds)
            y0 = z[0]
            ymax = z[1]
            um = z[2]
            l = z[3]
            A = np.log(ymax/y0)
            tm = ((A/(np.exp(1)*um))+l)   

            # Compute doubling time at peak growth
            ndt = 2
            dt = np.log(2)/um
            # Time range to consider exponential growth phase
            t1 = tm
            t2 = tm + ndt*dt

            print(f"samp : {si} of {len(grouped_df)} samples, t1: {t1}, t2: {t2}")

            if t1 > 0:
                idx = np.where((d_time >= t1) & (d_time <= t2))[0]
                t_rat = d_time.iloc[idx]
                d_rat = d_value.iloc[idx]
                x_rat = x_value.iloc[idx]
                y_rat = y_value.iloc[idx]

                zx = np.polyfit(d_rat, x_rat, 1)
                zy = np.polyfit(d_rat, y_rat, 1)

                dxda = zx[0]
                dyda = zy[0]
                rho = dyda/dxda
                data = samp.iloc[0]
                data['value'] = rho
                result = result.append(data, ignore_index=True)
        except:
            pass
    return result  
