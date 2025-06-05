import xarray as xr
import zipfile
from pathlib import Path

# Path to raw data
raw_dir = Path("7-days-MVP/raw")
date = "2025-06-05"

# Inspect the NetCDF file (air quality data)
nc_zip_path = raw_dir / f"{date}_cams_air_quality.nc.zip"
print("\n--- CAMS Air Quality Data (NetCDF) ---")
if nc_zip_path.exists():
    with zipfile.ZipFile(nc_zip_path, 'r') as zip_ref:
        # Extract the .nc file to memory
        nc_file = zip_ref.namelist()[0]
        with zip_ref.open(nc_file) as f:
            ds = xr.open_dataset(f)
            print(f"Dimensions: {ds.dims}")
            print(f"Variables: {list(ds.data_vars)}")
            print(f"Coordinates: {list(ds.coords)}")
            # Print a sample of the first variable
            first_var = list(ds.data_vars)[0]
            print(f"\nSample data for {first_var}:")
            print(ds[first_var].values.ravel()[:5])
else:
    print(f"File not found: {nc_zip_path}")

# Inspect the GRIB file (atmospheric composition)
grib_path = raw_dir / f"{date}_cams_atmos_composition.grib"
print("\n--- CAMS Atmospheric Composition Data (GRIB) ---")
if grib_path.exists():
    try:
        ds = xr.open_dataset(grib_path, engine='cfgrib')
        print(f"Dimensions: {ds.dims}")
        print(f"Variables: {list(ds.data_vars)}")
        print(f"Coordinates: {list(ds.coords)}")
        # Print a sample of the first variable
        first_var = list(ds.data_vars)[0]
        print(f"\nSample data for {first_var}:")
        print(ds[first_var].values.ravel()[:5])
    except Exception as e:
        print(f"Error loading GRIB file: {e}")
else:
    print(f"File not found: {grib_path}") 