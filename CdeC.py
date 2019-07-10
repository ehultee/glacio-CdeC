## Helper functions to clean up Clubes de Ciencia notebooks
## 5 July 2019  EHU
import xarray as xr
import pandas as pd
import numpy as np
from oggm import utils

def ice_to_freshwater(icevol, rho_ice=900, rho_water=1000):
    """Cleanly convert volume of glacial ice (km3) to equivalent volume fresh water (liter).
    Arguments:
        icevol = volume of ice to convert, in km3
        rho_ice = density of glacial ice (default 900 kg/m3)
        rho_water = density of freshwater (default 1000 kg/m3)
        """
    km3_to_ltr = 1E12
    water_vol_km3 = icevol * rho_ice / rho_water
    return water_vol_km3 * km3_to_ltr


def read_run_results(gdir, filesuffix=None):
    """Reads the output diagnostics of a simulation and puts the data in a pandas dataframe.
    
    Parameters
    ----------
    gdir : the glacier directory
    filesuffix : the file identifier 
    
    Returns
    -------
    a pandas Dataframe with monthly temp and precip
    """
    
    with xr.open_dataset(gdir.get_filepath('model_diagnostics', filesuffix=filesuffix)) as ds:
        ds = ds.load()
      
    # Lemgth needs filtering
    ts = ds.length_m.to_series()
    ts = ts.rolling(12*3).min()
    ts.iloc[0:12*3] = ts.iloc[12*3]
    
    # Volume change
    delta_vol = np.append([0], ds.volume_m3.data[1:] - ds.volume_m3.data[0:-1])
    
    odf = pd.DataFrame()
    odf['length_m'] = ts
    odf['volume_m3'] = ds.volume_m3
    odf['delta_water_m3'] = delta_vol * 0.9
    odf['month'] = ds.calendar_month
    
    return odf


def read_climate_statistics(gdir):
    """Reads the annual cycle of climate for [1985-2015] at the glacier terminus elevation.
    
    Parameters
    ----------
    gdir : the glacier directory
    
    Returns
    -------
    a pandas Dataframe with monthly average temp and precip
    """
    
    with xr.open_dataset(gdir.get_filepath('climate_monthly')) as ds:
        ds = ds.load()
        
    ds = ds.sel(time=slice('1985', '2015'))
        
    dsm = ds.groupby('time.month').mean(dim='time')
    odf = pd.DataFrame()
    odf['temp_celcius'] = dsm.temp.to_series()
    odf['prcp_mm_mth'] = dsm.prcp.to_series()
    
    # We correct for altitude difference
    d = utils.glacier_statistics(gdir)
    odf['temp_celcius'] += (ds.ref_hgt - d['flowline_min_elev']) * 0.0065
    
    return odf

