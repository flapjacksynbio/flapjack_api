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

remove_background = {
        'Velocity': False,
        'Expression Rate (indirect)': True
    }

class Analysis:
    def __init__(self, samples, params, signals):
        self.set_params(params)
        self.signals = signals
        # Functions to call for particular analysis types
        self.analysis_funcs = {
            'Velocity': self.velocity,
            'Expression Rate (indirect)': self.expression_rate_indirect
        }
        self.background = {}

    def set_params(self, params):
        self.analysis_type = params['type']
        self.density_name = params.get('biomass_signal')
        self.bg_std_devs = params.get('bg_correction')
        self.min_density = params.get('min_density')
        self.remove_data = params.get('remove_data')
        self.smoothing_type = params.get('smoothing_type', 'savgol')
        self.smoothing_param1 = int(params.get('pre_smoothing', 21))
        self.smoothing_param2 = int(params.get('post_smoothing', 21))

    def analyze_data(self, df):     
        # Is it necessary to remove background for this analysis?
        if remove_background[self.analysis_type]:
            df = self.bg_correct(df)
            
        # Apply analysis to dataframe
        analysis_func = self.analysis_funcs[self.analysis_type]
        df = analysis_func(df)
        return df

    def compute_background(self, assay, media, strain):
        s = Sample.objects.filter(assay__name__exact=assay) \
                            .filter(media__name__exact=media)
        samps_no_cells = s.filter(vector__name__in=['none', 'None']).filter(strain__name__in=['none', 'None'])
        samps_no_dna = s.filter(vector__name__in=['none', 'None']).filter(strain__name__exact=strain)
        meas_no_cells = get_measurements(samps_no_cells)
        meas_no_dna = get_measurements(samps_no_dna)

        # Compute media background
        bg_media = {}
        grouped_meas = meas_no_cells.groupby('Signal_id')
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
        grouped_meas = meas_no_dna.groupby('Signal_id')
        for name,data_meas in grouped_meas:
            vals = []
            grouped_samp = data_meas.groupby('Sample')
            for samp_id,data_samp in grouped_samp:
                data_samp = data_samp.sort_values('Time')
                vals.append(data_samp['Measurement'].values)
            vals = np.array(vals)
            bg_strain[name] = (np.mean(vals, axis=0), np.std(vals, axis=0))

        return bg_media,bg_strain

    def get_background(self, assay, media, strain):
        key = (assay, media, strain)
        if key not in self.background:
            self.background[key] = self.compute_background(assay, media, strain)
        return self.background[key]

    def bg_correct(self, df):
        # Empty dataframe to accumulate result
        meas_bg_corrected = pd.DataFrame()

        # Ignore background samples
        meas = df[~df.Vector.isin(['none','None'])]
        #get_measurements(self.samples.exclude(vector__name__in=['none', 'None']), signals)
        # Loop over samples
        rows = []
        grouped_sample = meas.groupby('Sample')
        for samp_id,sample_data in grouped_sample:
            assay = sample_data['Assay'].values[0]
            media = sample_data['Media'].values[0]
            strain = sample_data['Strain'].values[0]
            bg_media, bg_strain = self.get_background(assay, media, strain)
            grouped_name = sample_data.groupby('Signal_id')   
            # Loop over measurement names
            for name,meas_data in grouped_name:
                meas_data = meas_data.sort_values('Time')
                time = meas_data['Time']
                vals = meas_data['Measurement'].values
                if name==self.density_name:
                    # Correct OD
                    bg_media_mean, bg_media_std = bg_media.get(name, (0.,0.))
                    vals_corrected = vals - bg_media_mean
                    if self.remove_data:
                        print('Correcting OD bg', flush=True)
                        print('Removing %d data points'%np.sum(vals_corrected < self.bg_std_devs*bg_media_std), flush=True)
                        vals_corrected[vals_corrected < np.maximum(self.bg_std_devs*bg_media_std, min_density)] = np.nan
                    #print('bgmean, bgstd = ', bg_media_mean, bg_media_std)
                else:
                    # Correct fluorescence
                    bg_strain_mean, bg_strain_std = bg_strain.get(name, (0.,0.))
                    vals_corrected = vals - bg_strain_mean
                    if self.remove_data:
                        print('Correcting fluo bg', flush=True)
                        print('Removing %d data points'%np.sum(vals_corrected < self.bg_std_devs*bg_strain_std), flush=True)
                        vals_corrected[vals_corrected < self.bg_std_devs*bg_strain_std] = np.nan
                    #print('bgmean, bgstd = ', bg_strain_mean, bg_strain_std)

                # Remove all data at times earlier than the last NaN
                idx = np.where(np.isnan(vals_corrected[::-1]))[0]
                if len(idx)>0:
                    # Set all data before this time to NaN
                    vals_corrected[:len(vals_corrected)-idx[0]] = np.nan

                # Put values into dataframe
                meas_data = meas_data.assign(Measurement=vals_corrected)
                #meas_data['Measurement'] = vals_corrected
                rows.append(meas_data)

        if len(rows)>0:
            meas_bg_corrected = meas_bg_corrected.append(rows)        
        # Remove data meeting correction criteria
        if len(meas_bg_corrected)>0:
            meas_bg_corrected = meas_bg_corrected.dropna(subset=['Measurement'])
        return(meas_bg_corrected)

    # Analysis functions that compute timeseries from a dataframe with given keyword args
    # -----------------------------------------------------------------------------------
    def velocity(self, df):
        '''
        Parameters:
        df = data frame to analyse
        pre_smoothing = Savitsky-Golay filter parameter (window size)
        post_smoothing = Savitsky-Golay filter parameter (window size)
        '''
        print(self.smoothing_param1, self.smoothing_param2, flush=True)
        
        result = pd.DataFrame()
        rows = []

        if self.smoothing_type=='lowess':
            lowess = sm.nonparametric.lowess

        grouped_sample = df.groupby('Sample')
        n_samples = len(grouped_sample)
        # Loop over samples
        si = 1
        for samp_id, samp_data in grouped_sample:
            print('Computing velocity of sample %d of %d'%(si, n_samples), flush=True)
            si += 1
            for meas_name, data in samp_data.groupby('Signal_id'):
                data = data.sort_values('Time')
                time = data['Time'].values
                val = data['Measurement'].values
                
                if self.smoothing_type=='savgol':
                    min_data_pts = max(self.smoothing_param1, self.smoothing_param2)
                else:
                    min_data_pts = 2
                if len(val)>min_data_pts:
                    # Interpolation
                    ival = interp1d(time, val)
                    
                    # Savitzky-Golay filter
                    if self.smoothing_param1>0:
                        if self.smoothing_type=='savgol':
                            #print('Applying savgol filter', flush=True)
                            sval = savgol_filter(val, int(self.smoothing_param1), 2, mode='interp')
                            #print(len(val), flush=True)
                        elif smoothing_type=='lowess':
                            #print('Applying lowess filter', flush=True)
                            z = lowess(val, time, frac=self.smoothing_param1)
                            sval = z[:,1]
                            #print(len(val), flush=True)

                    # Interpolation
                    sval = interp1d(time, sval)

                    # Compute expression rate for time series
                    velocity = savgol_filter(ival(time), int(self.smoothing_param1), 2, deriv=1, mode='interp')
    
                    # Final Savitzky-Golay filtering of expression rate profile
                    if self.smoothing_param2>0:
                        if self.smoothing_type=='savgol':
                            velocity = savgol_filter(velocity, int(self.smoothing_param2), 2, mode='interp')
                        elif smoothing_type=='lowess':
                            z = lowess(velocity, time, frac=self.smoothing_param2)
                            ksynth = z[:,1]
                    # Put result in dataframe
                    data = data.assign(Measurement=velocity)
                    rows.append(data)
        if len(rows)>0:
            result = result.append(rows)
        else:
            print('No rows to add to velocity dataframe', flush=True)

        return(result)

    def expression_rate_indirect(self, df):
        '''
        Parameters:
        df = data frame to analyse
        density_df = dataframe with density measurements
        pre_smoothing = Savitsky-Golay filter parameter (window size)
        post_smoothing = Savitsky-Golay filter parameter (window size)
        '''
        print(self.smoothing_param1, self.smoothing_param2, flush=True)
        density_df = df[df['Signal_id']==self.density_name]
        
        result = pd.DataFrame()
        rows = []

        if self.smoothing_type=='lowess':
            lowess = sm.nonparametric.lowess

        grouped_sample = df.groupby('Sample')
        n_samples = len(grouped_sample)
        # Loop over samples
        si = 1
        for samp_id, samp_data in grouped_sample:
            print('Computing expression rate of sample %d of %d'%(si, n_samples), flush=True)
            si += 1
            for meas_name, data in samp_data.groupby('Signal_id'):
                data = data.sort_values('Time')
                time = data['Time'].values
                val = data['Measurement'].values
                density = density_df[density_df['Sample']==samp_id]
                density = density.sort_values('Time')
                density_val = density['Measurement'].values
                density_time = density['Time'].values
                
                if self.smoothing_type=='savgol':
                    min_data_pts = max(self.smoothing_param1, self.smoothing_param2)
                else:
                    min_data_pts = 2
                print(len(val), flush=True)
                if len(val)>min_data_pts and len(density_val)>min_data_pts:
                    # Interpolation
                    ival = interp1d(time, val)
                    idensity = interp1d(density_time, density_val)

                    # Savitzky-Golay filter
                    if self.smoothing_param1>0:
                        if self.smoothing_type=='savgol':
                            print('Applying savgol filter', flush=True)
                            sval = savgol_filter(val, int(self.smoothing_param1), 2, mode='interp')
                            sdensity = savgol_filter(density_val, int(self.smoothing_param1), 2, mode='interp')
                            print(len(val), len(density_val), flush=True)
                        elif smoothing_type=='lowess':
                            print('Applying lowess filter', flush=True)
                            z = lowess(val, time, frac=self.smoothing_param1)
                            sval = z[:,1]
                            z = lowess(density_val, density_time, frac=self.smoothing_param1)
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
                    data = data[ (data.Time>=tmin) & (data.Time<tmax) ]

                    # Compute expression rate for time series
                    dvaldt = savgol_filter(ival(time), int(self.smoothing_param1), 2, deriv=1, mode='interp')
                    ksynth = dvaldt / sdensity(time)
                    #dvaldt = sval.derivative()(time)
                    #ksynth = dvaldt / (sdensity(time) + 0.)

                    # Compute promoter activity d/dt(I/A)
                    #conc = sval(time) / sdensity(time)
                    #sconc = UnivariateSpline(time, conc, s=0, k=3)
                    #ksynth = sconc.derivative()(time)
    
                    # Final Savitzky-Golay filtering of expression rate profile
                    if self.smoothing_param2>0:
                        if self.smoothing_type=='savgol':
                            ksynth = savgol_filter(ksynth, int(self.smoothing_param2), 2, mode='interp')
                        elif smoothing_type=='lowess':
                            z = lowess(ksynth, time, frac=self.smoothing_param2)
                            ksynth = z[:,1]
                    # Put result in dataframe
                    data = data.assign(Measurement=ksynth)
                    rows.append(data)
        if len(rows)>0:
            result = result.append(rows)
        else:
            print('No rows to add to expression rate dataframe', flush=True)

        return(result)