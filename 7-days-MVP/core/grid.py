#!/usr/bin/env python3
"""
Grid harmonization module for SkyWell.
Reprojects CAMS and Sentinel-3 data to a common 0.01° grid and saves as COG files.
"""

import xarray as xr
import rioxarray as rio
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import zipfile
import tempfile
import shutil
# import cfgrib # Commented out as not needed for NetCDF

# Constants
GRID_RESOLUTION = 0.01  # degrees
BERLIN_BOUNDS = {
    'north': 52.75,
    'south': 52.25,
    'east': 13.85,
    'west': 13.05
}

def create_target_grid():
    """Create a target grid for Berlin with 0.01° resolution."""
    lats = np.arange(BERLIN_BOUNDS['south'], BERLIN_BOUNDS['north'] + GRID_RESOLUTION, GRID_RESOLUTION)
    lons = np.arange(BERLIN_BOUNDS['west'], BERLIN_BOUNDS['east'] + GRID_RESOLUTION, GRID_RESOLUTION)
    print(f"Created target grid with dimensions: {len(lats)}x{len(lons)}")
    return lats, lons

def validate_interpolation(source_data, interpolated_data, var_name):
    """Validate interpolation results."""
    # Print ranges for debugging (keep for diagnostics if needed)
    source_min, source_max = np.nanmin(source_data), np.nanmax(source_data)
    interp_min, interp_max = np.nanmin(interpolated_data), np.nanmax(interpolated_data)
    print(f"Debug Validation - {var_name}: Source range ({source_min:.5f}, {source_max:.5f}), Interpolated range ({interp_min:.5f}, {interp_max:.5f})")

    # Check for NaN values in interpolated data
    if np.any(np.isnan(interpolated_data)):
        print(f"Warning: Interpolated {var_name} contains NaN values!")
        return False
    
    # Check for all zeros in interpolated data:
    # If source is all zeros, interpolated should also be all zeros (and pass)
    if np.all(source_data == 0):
        return np.all(interpolated_data == 0)

    # If source is NOT all zeros, but interpolated IS all zeros, then it's a failure
    if np.all(interpolated_data == 0) and not np.all(source_data == 0):
        print(f"Warning: Interpolated {var_name} contains all zeros but source data does not!")
        return False
    
    # If we reach here, it means no NaNs and not all zeros (unless source was all zeros and interpolated matched).
    # We are now trusting the interpolation if it produces valid non-zero values.
    return True

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
            ds = xr.open_dataset(nc_path, engine='netcdf4')
            print(f"Source data dimensions: {ds.dims}")
            
            # Create target grid
            target_lats, target_lons = create_target_grid()
            
            # Process each variable
            for var in ds.data_vars:
                # Skip non-environmental variables
                if var in ['longitude', 'latitude', 'time']:
                    continue
                    
                print(f"\nProcessing {var}...")
                # Get the data for the first time step (current forecast)
                data = ds[var].isel(time=0)

                print(f"Source data shape: {data.shape}")
                if np.any(np.isnan(data.values)):
                    print(f"Warning: Source data for {var} contains NaN values before interpolation!")
                
                # Create a template DataArray for interpolation
                template_da = xr.DataArray(
                    np.empty((len(target_lats), len(target_lons))),
                    coords={'latitude': target_lats, 'longitude': target_lons},
                    dims=['latitude', 'longitude']
                )
                
                # Interpolate to target grid using interp_like
                target_data = data.interp_like(template_da, method='linear')
                
                # Assign the interpolated data to the target dataset
                target_ds = xr.Dataset(
                    coords={
                        'latitude': target_lats,
                        'longitude': target_lons
                    }
                )
                
                # Assign the interpolated data to the target dataset
                target_ds[var] = target_data
                
                # Validate interpolation
                if not validate_interpolation(data.values, target_ds[var].values, var):
                    print(f"Skipping {var} due to validation failure")
                    continue
                
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
        ds = xr.open_dataset(grib_path, engine='cfgrib')
        print(f"Source UVI data dimensions: {ds.dims}")

        # The variable name for UV biologically effective dose is 'uvbed' in the GRIB file
        uvi_data = ds['uvbed'].isel(step=0)
        print(f"Source UVI data shape: {uvi_data.shape}")

        # Create target grid
        target_lats, target_lons = create_target_grid()

        # Interpolate to target grid
        uvi_interpolated = uvi_data.interp(
            latitude=target_lats,
            longitude=target_lons,
            method='linear'
        )

        # Validate interpolation
        if not validate_interpolation(uvi_data.values, uvi_interpolated.values, 'uv_biologically_effective_dose'):
            print("Skipping UVI data due to validation failure")
            return

        # Create a new DataArray with the target grid
        target_da = xr.DataArray(
            uvi_interpolated.values,
            coords=[target_lats, target_lons],
            dims=['latitude', 'longitude'],
            name='uv_biologically_effective_dose'
        )

        # Convert to rioxarray and save as COG
        output_path = Path('data') / f"{date}_uv_biologically_effective_dose.tif"
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
        print(f"Loaded {var_name} with shape {grid_data[var_name].shape}")
    
    return grid_data

def main():
    """Main function to process today's data."""
    today = datetime.utcnow().date()
    date_str = today.strftime('%Y-%m-%d')
    
    # Process CAMS air quality and pollen data (NetCDF)
    cams_zip = Path('raw') / f"{date_str}_cams_air_quality.nc.zip"
    if cams_zip.exists():
        process_cams_data(cams_zip, date_str)
    else:
        print(f"CAMS air quality and pollen data not found: {cams_zip}")

    # Process CAMS Global UVI data (GRIB)
    # uvi_grib = Path('raw') / f"{date_str}_cams_atmos_composition.grib"
    # if uvi_grib.exists():
    #     process_cams_global_uvi_data(uvi_grib, date_str)
    # else:
    #     print(f"CAMS Global UVI data not found: {uvi_grib}")

    # Note: Sentinel-3 UV data processing is removed as we are using CAMS UVI.
    # The placeholder function process_sentinel3_data remains but does nothing.

if __name__ == "__main__":
    main() 