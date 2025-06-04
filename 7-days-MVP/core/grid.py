#!/usr/bin/env python3
"""
Grid harmonization module for SkyWell.
Reprojects CAMS and Sentinel-3 data to a common 0.01° grid and saves as COG files.
"""

import xarray as xr
import rioxarray as rio
import numpy as np
from pathlib import Path
from datetime import datetime
import zipfile
import tempfile
import shutil
# Import cfgrib for reading GRIB files
import cfgrib

# Constants
GRID_RESOLUTION = 0.01  # degrees
BERLIN_BOUNDS = {
    'north': 53.0,
    'south': 52.3,
    'east': 14.0,
    'west': 13.0
}

def create_target_grid():
    """Create a target grid for Berlin with 0.01° resolution."""
    lats = np.arange(BERLIN_BOUNDS['south'], BERLIN_BOUNDS['north'] + GRID_RESOLUTION, GRID_RESOLUTION)
    lons = np.arange(BERLIN_BOUNDS['west'], BERLIN_BOUNDS['east'] + GRID_RESOLUTION, GRID_RESOLUTION)
    return lats, lons

def extract_cams_netcdf(zip_path):
    """Extract the NetCDF file from the CAMS zip archive and copy it to raw/ for persistence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)
            # Find the .nc file in the extracted contents
            nc_files = list(Path(tmpdir).glob('*.nc'))
            if not nc_files:
                raise ValueError(f"No NetCDF file found in {zip_path}")
            extracted_nc = nc_files[0]
            # Copy the extracted file to raw/ for persistence
            persistent_nc = Path('raw') / extracted_nc.name
            shutil.copy(extracted_nc, persistent_nc)
            return persistent_nc

def process_cams_data(zip_path, date):
    """Process CAMS data and save individual variables as COG files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Extract the NetCDF file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)
            # Find the .nc file in the extracted contents
            nc_files = list(Path(tmpdir).glob('*.nc'))
            if not nc_files:
                raise ValueError(f"No NetCDF file found in {zip_path}")
            nc_path = nc_files[0]
            
            # Open and process the NetCDF file within the temporary directory context
            ds = xr.open_dataset(nc_path)
            
            # Create target grid
            target_lats, target_lons = create_target_grid()
            
            # Process each variable
            for var in ds.data_vars:
                # Skip non-environmental variables
                if var in ['longitude', 'latitude', 'time']:
                    continue
                    
                # Get the data for the first time step (current forecast)
                data = ds[var].isel(time=0)
                
                # Create a new dataset with the target grid
                target_ds = xr.Dataset(
                    coords={
                        'latitude': target_lats,
                        'longitude': target_lons
                    }
                )
                
                # Interpolate to target grid
                target_ds[var] = data.interp(
                    latitude=target_lats,
                    longitude=target_lons,
                    method='linear'
                )
                
                # Save as COG
                output_path = Path('data') / f"{date}_{var}.tif"
                output_path.parent.mkdir(exist_ok=True)
                
                # Convert to rioxarray and save as COG
                target_ds[var].rio.to_raster(
                    output_path,
                    driver='COG',
                    compress='LZW'
                )
                
                print(f"Saved {var} to {output_path}")
            
            # Close the dataset to free up resources
            ds.close()

def process_cams_global_uvi_data(grib_path, date):
    """Process CAMS Global UVI data from GRIB and save as COG file."""
    print(f"Processing UVI data from {grib_path}...")
    try:
        # Open the GRIB file using xarray with the cfgrib engine
        # Use .isel(step=0) to get the first forecast time step if multiple are present
        ds = xr.open_dataset(grib_path, engine='cfgrib')

        # Assuming the variable name for UVI is 'uvbed'
        # You might need to verify this from the grib file inspection if necessary.
        uvi_data = ds['uvbed'].isel(step=0)

        # Create target grid
        target_lats, target_lons = create_target_grid()

        # Interpolate to target grid
        # Ensure the UVI data has latitude and longitude dimensions correctly named
        # and ordered if necessary, though xarray often handles this.
        uvi_interpolated = uvi_data.interp(
            latitude=target_lats,
            longitude=target_lons,
            method='linear'
        )

        # Create a new DataArray with the target grid and original variable name
        target_da = xr.DataArray(
            uvi_interpolated.values,
            coords=[target_lats, target_lons],
            dims=['latitude', 'longitude'],
            name='uvbed' # Use the original variable name
        )

        # Convert to rioxarray and save as COG
        output_path = Path('data') / f"{date}_uvbed.tif"
        output_path.parent.mkdir(exist_ok=True)

        target_da.rio.to_raster(
            output_path,
            driver='COG',
            compress='LZW'
        )

        print(f"Saved UVI data to {output_path}")

        ds.close()

    except Exception as e:
        print(f"Error processing UVI data: {e}")

def process_sentinel3_data(zip_path, date):
    """Process Sentinel-3 UV data and save as COG file."""
    # This function is no longer needed as we are not using Sentinel-3 for UV
    pass # Keep as a placeholder for now or remove if completely sure

def load_grid(date):
    """Load all variables for a given date into a dictionary of numpy arrays."""
    data_dir = Path('data')
    date_str = date.strftime('%Y-%m-%d')
    
    # Find all files for this date
    files = list(data_dir.glob(f"{date_str}_*.tif"))
    
    if not files:
        raise ValueError(f"No data found for date {date_str}")
    
    # Load each file into a dictionary
    grid_data = {}
    for file in files:
        var_name = file.stem.split('_', 1)[1]  # Get variable name from filename
        ds = rio.open_rasterio(file)
        grid_data[var_name] = ds.values[0]  # Get first band
    
    return grid_data

def main():
    """Main function to process today's data."""
    today = datetime.utcnow().date()
    date_str = today.strftime('%Y-%m-%d')
    
    # Process CAMS air quality and pollen data (NetCDF)
    cams_zip = Path('raw') / f"{date_str}_cams.nc.zip"
    if cams_zip.exists():
        process_cams_data(cams_zip, date_str)
    else:
        print(f"CAMS air quality and pollen data not found: {cams_zip}")

    # Process CAMS Global UVI data (GRIB)
    uvi_grib = Path('raw') / f"{date_str}_cams_uvi.grib"
    if uvi_grib.exists():
        process_cams_global_uvi_data(uvi_grib, date_str)
    else:
        print(f"CAMS Global UVI data not found: {uvi_grib}")

    # Note: Sentinel-3 UV data processing is removed as we are using CAMS UVI.
    # The placeholder function process_sentinel3_data remains but does nothing.

if __name__ == "__main__":
    main() 