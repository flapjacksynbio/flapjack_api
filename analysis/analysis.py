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
        'Mean Velocity': False,
        'Max Velocity': False,
        'Expression Rate (indirect)': False,
        'Expression Rate (direct)': False,
        'Mean Expression': True,
        'Max Expression': True,
        'Induction Curve': True,
        'Kymograph': True
    }

class Analysis:
    def __init__(self, params, signals):
        self.set_params(params)
        self.signals = signals
        # Functions to call for particular analysis types
        self.analysis_funcs = {
            'Velocity': self.velocity,
            'Expression Rate (indirect)': self.expression_rate_indirect,
            'Expression Rate (direct)': self.expression_rate_direct,
            'Mean Velocity': self.mean_velocity,
            'Max Velocity': self.max_velocity,
            'Mean Expression': self.mean_expression,
            'Max Expression': self.max_expression,
            'Induction Curve': self.induction_curve,
            'Kymograph': self.kymograph
        }
        self.background = {}

    def set_params(self, params):
        self.analysis_type = params['type']
        self.density_name = params.get('biomass_signal')
        self.bg_std_devs = params.get('bg_correction')
        self.min_density = float(params.get('min_density', 0))
        self.remove_data = params.get('remove_data')
        self.smoothing_type = params.get('smoothing_type', 'savgol')
        self.smoothing_param1 = int(params.get('pre_smoothing', 21))
        self.smoothing_param2 = int(params.get('post_smoothing', 21))
        self.degr = float(params.get('degr', 0.))
        self.eps_L = float(params.get('eps_L', 1e-7))
        chemical = params.get('chemical', None)
        if chemical:
            self.chemical_id = chemical['value']
        self.ref_name = params.get('ref_signal')

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
                        vals_corrected[vals_corrected < np.maximum(self.bg_std_devs*bg_media_std, self.min_density)] = np.nan
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
                    data = data.assign(Velocity=velocity)
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
                    data = data.assign(Rate=ksynth)
                    rows.append(data)
        if len(rows)>0:
            result = result.append(rows)
        else:
            print('No rows to add to expression rate dataframe', flush=True)

        return(result)

    def expression_rate_direct(self, df):
        '''
        Parameters:
            df = data frame to analyse
            density_df = dataframe containing density (biomass) measurements
            degr = degradation rate of reporter protein
            eps_L = insignificant value for model fitting
        '''
        if len(df)==0:
            return(df)

        density_df = df[df['Signal_id']==self.density_name]
        print(self.degr, self.eps_L, flush=True)
        print(density_df, flush=True)
        
        result = pd.DataFrame()
        rows = []

        grouped_sample = df.groupby('Sample')
        n_samples = len(grouped_sample)
        # Loop over samples
        si = 1
        for samp_id, samp_data in grouped_sample:
            print('Computing expression rate of sample %d of %d'%(si, n_samples), flush=True)
            si += 1
            for meas_name, data in samp_data.groupby('Signal_id'):
                data = data.sort_values('Time')
                time = data['Time']
                val = data['Measurement']
                density = density_df[density_df['Sample']==samp_id]
                density = density.sort_values('Time')
                density_val = density['Measurement']
                density_time = density['Time']

                if len(val)>1:
                    # Construct curves
                    fpt = time.values
                    fpy = val.values
                    cfp = wf.curves.Curve(x=fpt, y=fpy)
                    odt = density_time.values
                    ody = density_val.values
                    cod = wf.curves.Curve(x=odt, y=ody)
                    # Compute time range
                    od_xmin, od_xmax = cod.xlim()
                    cfp_xmin, cfp_xmax = cfp.xlim()
                    xmin = max(od_xmin, cfp_xmin)
                    xmax = min(od_xmax, cfp_xmax)
                    ttu = np.arange(od_xmin, od_xmax, 0.1)
                    # Fit model
                    try:
                        if meas_name==self.density_name:
                            ksynth, _, _, _, _ = wf.infer_growth_rate(cod, ttu, 
                                                                        eps_L=self.eps_L, 
                                                                        positive=True)
                        else:
                            ksynth, _, _, _, _ = wf.infer_synthesis_rate_onestep(cfp, cod, ttu, 
                                                                                    degr=self.degr, eps_L=self.eps_L, 
                                                                                    positive=True)
                        data = data.assign(Rate=ksynth(fpt))
                        rows.append(data)
                    except:
                        pass
        if len(rows)>0:
            result = result.append(rows)
            result = result.dropna(subset=['Rate'])
        else:
            print('No rows to add to expression rate dataframe', flush=True)
        return(result)

    # Analysis functions that compute value from a dataframe with given keyword args
    # ----------------------------------------------------------------------------------
    def mean_expression(self, df):
        '''
        Return a dataframe containing the mean value for each sample,name in the input dataframe df
        '''
        agg = {}
        for column_name in df.columns:
            if column_name!='Sample' and column_name!='Signal':
                agg[column_name] = 'first'
        agg['Measurement'] = 'mean'
        grouped_samples = df.groupby(['Sample', 'Signal'], as_index=False)
        mean = grouped_samples.agg(agg)
        mean.columns = ['Expression' if c=='Measurement' else c for c in mean.columns]
        return mean     

    def max_expression(self, df):
        '''
        Return a dataframe containing the mean value for each sample,name in the input dataframe df
        '''
        agg = {}
        for column_name in df.columns:
            if column_name!='Sample' and column_name!='Signal':
                agg[column_name] = 'first'
        agg['Measurement'] = 'max'
        grouped_samples = df.groupby(['Sample', 'Signal'], as_index=False)
        maxx = grouped_samples.agg(agg)
        maxx.columns = ['Expression' if c=='Measurement' else c for c in mean.columns]
        return maxx     

    def mean_velocity(self, df):
        '''
        Return a dataframe containing the max value for each sample,name in the input dataframe df
        '''
        df = self.velocity(df)
        agg = {}
        for column_name in df.columns:
            if column_name!='Sample' and column_name!='Signal':
                agg[column_name] = 'first'
        agg['Velocity'] = 'mean'
        grouped_samples = df.groupby(['Sample', 'Signal'], as_index=False)
        mean_expr = grouped_samples.agg(agg)
        return mean_expr    

    def max_velocity(self, df):
        '''
        Return a dataframe containing the max velocity for each sample,name in the input dataframe df
        '''
        df = self.velocity(df)
        agg = {}
        for column_name in df.columns:
            if column_name!='Sample' and column_name!='Signal':
                agg[column_name] = 'first'
        agg['Velocity'] = 'max'
        grouped_samples = df.groupby(['Sample', 'Signal'], as_index=False)
        max_expr = grouped_samples.agg(agg)
        return max_expr    

    # Other analysis types that make different forms of resulting data
    def induction_curve(self, df):
        data = df[df.Chemical_id==self.chemical_id]
        mean_expr = self.mean_expression(data)
        return mean_expr

    def kymograph(self, df):
        '''
        Compute kymograph for induced expression, x-axis=inducer concentration
        '''
        data = df[df.Chemical_id==self.chemical_id]
        return data

    def ratiometric_alpha(self, df):
        # Parameters:
        #   bounds = tuple of list of min and max values for  Gompertz model parameters
        #   df = dataframe of measurements including OD
        #   density_df = dataframe containing biomass measurements
        #   ndt = number of doubling times to extend exponential phase
        density_df = df[df['Signal_id']==density_name]

        result = pd.DataFrame()
        rows = []

        grouped_samples = df.groupby('Sample')
        for samp_id,data in grouped_samples:
            # input values for Gompertz model fit
            oddf = density_df[density_df['Sample']==samp_id]
            oddf = oddf.sort_values('Time')
            odt = oddf['Time'].values
            odval = oddf['Measurement'].values
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
            grouped_name = data.groupby('Signal')
            for name,data in grouped_name:
                # fluorescence measurements
                mdf = data[(data['Time']>=t1) & (data['Time']<=t2)]
                mdf = mdf.sort_values('Time')
                mval = mdf['Measurement'].values
                mt = mdf['Time'].values
                
                # od measurements
                oddf = oddf[(oddf['Time']>=t1)&(oddf['Time']<=t2)]
                oddf = oddf.sort_values('Time')
                odval = oddf['Measurement'].values
                odt = oddf['Time'].values
                
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

    def ratiometric_rho(self, df):
        # Parameters:
        #   bounds = tuple of list of min and max values for  Gompertz model parameters
        #   df = dataframe of measurements including OD
        #   density_df = dataframe containing biomass measurements
        #   ref_df = dataframe containing reference measurements
        #   ndt = number of doubling times to extend exponential phase
        density_df = df[df['Signal_id']==self.density_name]
        ref_df = df[df['Signal_id']==self.ref_name]

        alpha = self.ratiometric_alpha(df)
        alpha_ref = self.ratiometric_alpha(ref_df)

        alpha = alpha.sort_values('Sample')
        alpha_ref = alpha_ref.sort_values('Sample')

        result = pd.DataFrame()
        rows = [] 
        grouped = alpha.groupby('Signal')
        # Normalise each measurement separately by the reference
        for name_id,data in grouped:
            data = data.sort_values('Sample')
            vals = data['Measurement'].values
            ref = alpha_ref['Measurement'].values
            data['Measurement'] = vals / ref
            rows.append(data)
        result = result.append(rows)
        return result     

