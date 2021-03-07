import numpy as np
from scipy.optimize import least_squares
from scipy.interpolate import interp1d

# Inverse method for expression rate
#
def forward_model(
    Dt=0.25,
    sim_steps=1,
    odval=[1]*97,
    profile=[1]*97,
    gamma=0,
    p0=0,
    nt=100
):
    p1_list,od_list, A_list,t_list = [],[],[],[]
    p1 = p0
    for t in range(nt):
        p1_list.append(p1)
        t_list.append([t * Dt])
        od = odval[t]
        tt = t*Dt
        prof = profile[t]
        for tt in range(sim_steps):
            nextp1 = p1 + (odval[t]*profile[t] - gamma*p1) * Dt / sim_steps
            p1 = nextp1


    ap1 = np.array(p1_list).transpose()
    tt = np.array(t_list).transpose()
    t = np.arange(nt) * Dt
    return ap1,tt

def residuals(data, p0, odval, dt, t, n_gaussians, epsilon, gamma): 
    def func(x): 
        nt = len(t)
        means = np.linspace(t.min(), t.max(), n_gaussians)
        vars = [(t.max()-t.min())/n_gaussians]*n_gaussians 
        p0 = x[0]
        heights = x[1:]
        profile = np.zeros_like(t)
        for mean,var,height in zip(means, vars, heights):
            gaussian = height * np.exp(-(t-mean)*(t-mean) / var / 2) / np.sqrt(2 * np.pi * var)
            profile = profile + gaussian
        p,tt = forward_model(
                    Dt=dt,
                    odval=odval,
                    profile=profile,
                    nt=nt,
                    p0=p0,
                    gamma=gamma
                )
        model = p[1:]
        tikhonov = heights * epsilon
        residual = data[1:] - model
        return np.concatenate((residual, tikhonov))
    return func

def characterize(expression, biomass, t, gamma, n_gaussians, epsilon):
    dt = np.diff(t).mean()
    nt = len(t)

    # Bounds for fitting
    lower_bounds = [0] + [0]*n_gaussians
    upper_bounds = [1e8] + [1e8]*n_gaussians
    bounds = [lower_bounds, upper_bounds]
    '''
        p0 = x[0]
        profile = x[1:]
    '''
    residuals_func = residuals(
                expression, 
                expression[0],
                biomass, 
                epsilon=epsilon, 
                dt=dt, 
                t=t, 
                n_gaussians=n_gaussians,
                gamma=gamma
                )
    res = least_squares(
            residuals_func, 
            [0] + [100]*n_gaussians, 
            bounds=bounds
            )
    res = res

    p0 = res.x[0]

    profile = np.zeros_like(t)
    means = np.linspace(t.min(), t.max(), n_gaussians)
    vars = [(t.max()-t.min())/n_gaussians] * n_gaussians 
    heights = res.x[1:]
    for mean,var,height in zip(means, vars, heights):
        gaussian = height * np.exp(-(t-mean)*(t-mean) / var / 2) / np.sqrt(2 * np.pi * var)
        profile = profile + gaussian
    profile = interp1d(t, profile, fill_value='extrapolate', bounds_error=False)
    return profile

# Inverse method for growth rate
#
def forward_model_growth(
    Dt=0.05,
    sim_steps=1,
    muval=[0]*100,
    od0=0,
    nt=100
):
    od_list, t_list = [],[]
    od = od0
    for t in range(nt):
        od_list.append(od)
        t_list.append([t * Dt])
        mu = muval[t]
        for tt in range(sim_steps):
            doddt = mu * od
            nextod = od + doddt * Dt/sim_steps
            od = nextod


    aod = np.array(od_list).transpose()
    tt = np.array(t_list).transpose()
    return aod,tt


def residuals_growth(data, epsilon, dt, t, n_gaussians): 
    def func(x): 
        od0 = x[0]
        muval = np.zeros_like(t)
        means = np.linspace(t.min(), t.max(), n_gaussians)
        vars = [(t.max()-t.min())/n_gaussians] * n_gaussians 
        heights = x[1:]
        for mean,var,height in zip(means, vars, heights):
            gaussian = height * np.exp(-(t-mean)*(t-mean) / var / 2) / np.sqrt(2 * np.pi * var)
            muval = muval + gaussian

        od,tt = forward_model_growth(
                    Dt=dt,
                    muval=muval,
                    od0=od0,
                    nt=len(t)
                )
        model = od
        residual = (data - model)  # / tt.ravel()[1:]
        tikhonov = heights
        result = np.concatenate((residual, epsilon * tikhonov))
        return result
    return func


def characterize_growth(
        biomass,
        t, 
        n_gaussians, 
        epsilon
        ):
    # Characterize growth rate profile
    dt = np.mean(np.diff(t))
    nt = len(t)

    lower_bounds = [0] + [0]*n_gaussians
    upper_bounds = [100] + [50]*n_gaussians
    bounds = [lower_bounds, upper_bounds]

    data = biomass
    res = least_squares(
            residuals_growth(data, epsilon=epsilon, dt=dt, t=t, n_gaussians=n_gaussians), 
            [0.01] + [1]*n_gaussians, 
            bounds=bounds
            )
    init_biomass = res.x[0]
    profile = np.zeros_like(t)
    means = np.linspace(t.min(), t.max(), n_gaussians)
    vars = [(t.max()-t.min())/n_gaussians] * n_gaussians 
    heights = res.x[1:]
    for mean,var,height in zip(means, vars, heights):
        gaussian = height * np.exp(-(t-mean)*(t-mean) / var / 2) / np.sqrt(2 * np.pi * var)
        profile = profile + gaussian
    mu_profile = interp1d(t, profile, fill_value='extrapolate', bounds_error=False)

    return mu_profile

