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
import os
from scipy.interpolate import RegularGridInterpolator
import re
import pandas as pd
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
            persistent_nc = Path('raw/cams') / extracted_nc.name
            shutil.copy(extracted_nc, persistent_nc)
            return persistent_nc

def process_cams_data(ds, target_lats, target_lons, output_dir, date_str):
    """Process CAMS data and interpolate to target grid."""
    os.makedirs(output_dir, exist_ok=True)
    for var in ds.data_vars:
        if var in ['longitude', 'latitude', 'time']:
            continue
        print(f"\nProcessing {var}...")
        try:
            data = ds[var].isel(time=0).squeeze()
            print(f"Source data shape: {data.shape}")
            if np.any(np.isnan(data.values)):
                print(f"Warning: Source data for {var} contains NaN values before interpolation!")
            source_lats = data.latitude.values
            source_lons = data.longitude.values
            interpolator = RegularGridInterpolator(
                (source_lats, source_lons),
                data.values,
                method='linear',
                bounds_error=False,
                fill_value=None
            )
            target_lon_grid, target_lat_grid = np.meshgrid(target_lons, target_lats)
            target_points = np.stack([target_lat_grid.flatten(), target_lon_grid.flatten()], axis=1)
            target_data = interpolator(target_points).reshape(target_lat_grid.shape)
            if not validate_interpolation(data.values, target_data, var):
                print(f"Warning: Interpolation validation failed for {var}")
                continue
            output_ds = xr.Dataset(
                data_vars={var: (['latitude', 'longitude'], target_data)},
                coords={'latitude': target_lats, 'longitude': target_lons}
            )
            output_path = Path(output_dir) / f"{date_str}_{var}.tif"
            output_ds[var].rio.to_raster(
                output_path,
                driver='COG',
                compress='LZW'
            )
            print(f"Saved {var} to {output_path}")
        except Exception as e:
            print(f"Error processing {var}: {str(e)}")
            continue

def process_sentinel3_data(zip_path, date):
    """Process Sentinel-3 UV data and save as COG file."""
    # This function is no longer needed as we are not using Sentinel-3 for UV
    pass # Keep as a placeholder for now or remove if completely sure

def process_uv_geotiff(uv_tif_path, target_lats, target_lons, output_dir, date_str):
    """
    Process UV GeoTIFF at 0.1° and interpolate to 0.01° grid, saving as COG.
    Args:
        uv_tif_path (str or Path): Path to the 0.1° UV GeoTIFF
        target_lats (np.ndarray): Target latitude grid (0.01°)
        target_lons (np.ndarray): Target longitude grid (0.01°)
        output_dir (str or Path): Output directory for COG
        date_str (str): Date string for output filename
    """
    print(f"\nProcessing UV GeoTIFF: {uv_tif_path}")
    da = rio.open_rasterio(uv_tif_path)
    # Remove band dimension if present
    if da.ndim == 3:
        da = da.isel(band=0)
    source_lats = da.y.values
    source_lons = da.x.values
    # Ensure increasing order for interpolation
    if np.any(np.diff(source_lats) < 0):
        source_lats = source_lats[::-1]
        da = da[::-1, :]
    interpolator = RegularGridInterpolator(
        (source_lats, source_lons),
        da.values,
        method='linear',
        bounds_error=False,
        fill_value=None
    )
    target_lon_grid, target_lat_grid = np.meshgrid(target_lons, target_lats)
    target_points = np.stack([target_lat_grid.flatten(), target_lon_grid.flatten()], axis=1)
    target_data = interpolator(target_points).reshape(target_lat_grid.shape)
    if not validate_interpolation(da.values, target_data, 'uv_index'):
        print("Warning: Interpolation validation failed for uv_index")
        return
    output_ds = xr.Dataset(
        data_vars={'uv_index': (['latitude', 'longitude'], target_data)},
        coords={'latitude': target_lats, 'longitude': target_lons}
    )
    output_path = Path(output_dir) / f"{date_str}_uv_index.tif"
    output_ds['uv_index'].rio.to_raster(
        output_path,
        driver='COG',
        compress='LZW'
    )
    print(f"Saved harmonized UV index to {output_path}")

def process_uv_csv(uv_csv_path, target_lats, target_lons, output_dir, date_str):
    """
    Process raw UV CSV and interpolate to 0.01° grid, saving as COG.
    Args:
        uv_csv_path (str or Path): Path to the raw UV CSV
        target_lats (np.ndarray): Target latitude grid (0.01°)
        target_lons (np.ndarray): Target longitude grid (0.01°)
        output_dir (str or Path): Output directory for COG
        date_str (str): Date string for output filename
    """
    print(f"\nProcessing UV CSV: {uv_csv_path}")
    df = pd.read_csv(uv_csv_path)
    df["time"] = pd.to_datetime(df["time"])
    # Use the first time step for now (current UV index)
    current_time = pd.to_datetime(df['time']).min()
    current_data = df[df['time'] == current_time].copy()
    if current_data.empty:
        print("No current UV data available in CSV.")
        return
    lats = sorted(current_data['latitude'].unique())
    lons = sorted(current_data['longitude'].unique())
    uv_grid = np.zeros((len(lats), len(lons)))
    for i, lat in enumerate(lats):
        for j, lon in enumerate(lons):
            mask = (current_data['latitude'] == lat) & (current_data['longitude'] == lon)
            if mask.any():
                uv_grid[i, j] = current_data.loc[mask, 'uv_index'].iloc[0]
    da = xr.DataArray(
        uv_grid,
        coords={'latitude': lats, 'longitude': lons},
        dims=['latitude', 'longitude'],
        name='uv_index'
    )
    da = da.rio.write_crs("EPSG:4326")
    output_path = Path(output_dir) / f"{date_str}_uv_index.tif"
    output_path.parent.mkdir(exist_ok=True)
    da.rio.to_raster(
        output_path,
        driver='COG',
        compress='LZW'
    )
    print(f"Saved harmonized UV index to {output_path}")

def load_grid(date):
    """Load all variables for a given date into a dictionary of numpy arrays."""
    data_dir = Path('data/cams')
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
    """Main function to process all data."""
    import glob
    aq_files = sorted(glob.glob('raw/cams/*_cams_air_quality.nc.zip'))
    if aq_files:
        latest_aq = aq_files[-1]
        print(f"Using air quality file: {latest_aq}")
        # Extract date from filename (expects format YYYY-MM-DD_cams_air_quality.nc.zip)
        match = re.search(r'(\d{4}-\d{2}-\d{2})_cams_air_quality', latest_aq)
        if match:
            date_str = match.group(1)
        else:
            date_str = 'unknown_date'
        nc_path = extract_cams_netcdf(latest_aq)
        ds = xr.open_dataset(nc_path, engine='netcdf4')
        target_lats, target_lons = create_target_grid()
        process_cams_data(ds, target_lats, target_lons, 'data/cams', date_str)
        ds.close()
        # --- Process UV GeoTIFF ---
        uv_tif_path = Path('data/cams') / f"{date_str}_uv_index.tif"
        if uv_tif_path.exists():
            process_uv_geotiff(uv_tif_path, target_lats, target_lons, 'data/cams', date_str)
        else:
            print(f"No UV GeoTIFF found for {date_str} at {uv_tif_path}")
    else:
        print("No CAMS air quality and pollen data file found in raw/cams/ directory.")
    # UVI section remains commented out
    uv_csv_files = sorted(glob.glob('raw/uv/uv_forecast_*.csv'))
    if uv_csv_files:
        latest_uv_csv = uv_csv_files[-1]
        process_uv_csv(latest_uv_csv, target_lats, target_lons, 'data/uv', date_str)
    else:
        print(f"No UV CSV found in raw/uv/ for {date_str}")

if __name__ == "__main__":
    main() 