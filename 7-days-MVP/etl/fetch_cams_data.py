#!/usr/bin/env python3
"""
Fetch CAMS air quality, pollen, and UVI data and save to raw/ directory.
This script downloads forecast data as NetCDF and GRIB for selected variables and times.
"""

import cdsapi
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import xarray as xr

# Load .env for local development
load_dotenv()

RAW_DIR = Path(__file__).parent.parent / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# CAMS Air Quality Forecasts
CAMS_AIR_QUALITY_DATASET = "cams-europe-air-quality-forecasts"
CAMS_AIR_QUALITY_VARIABLES = [
    "alder_pollen",
    "birch_pollen",
    "grass_pollen",
    "mugwort_pollen",
    "nitrogen_dioxide",
    "olive_pollen",
    "ozone",
    "particulate_matter_2.5um",
    "particulate_matter_10um",
    "ragweed_pollen",
    "sulphur_dioxide"
]
CAMS_AIR_QUALITY_MODEL = ["ensemble"]
CAMS_AIR_QUALITY_TIMES = ["00:00"]  # Only 00:00 as we use leadtime_hour for other times
CAMS_AIR_QUALITY_LEADTIME_HOUR = [
    "0", "8", "12", "16", "20",
    "24", "32", "36", "40", "44",
    "48", "56", "60", "64", "68",
    "72", "80", "84", "88", "92", "96"
]
CAMS_AIR_QUALITY_TYPE = ["forecast"]
CAMS_AIR_QUALITY_LEVEL = ["0"] # metres above surface
CAMS_AIR_QUALITY_AREA = [53, 13, 52, 14] # North, West, South, East

# CAMS Atmospheric Composition Forecasts
CAMS_ATMOS_COMPOSITION_DATASET = "cams-global-atmospheric-composition-forecasts"
CAMS_ATMOS_COMPOSITION_VARIABLE = ["uv_biologically_effective_dose"]
CAMS_ATMOS_COMPOSITION_TIMES = ["00:00"]  # Only 00:00 as we use leadtime_hour for other times
CAMS_ATMOS_COMPOSITION_LEADTIME_HOUR = [
    "0", "8", "12", "16", "20",
    "24", "32", "36", "40", "44",
    "48", "56", "60", "64", "68",
    "72", "80", "84", "88", "92", "96"
]
CAMS_ATMOS_COMPOSITION_TYPE = ["forecast"]
CAMS_ATMOS_COMPOSITION_AREA = [53, 13, 52, 14] # North, West, South, East

def fetch_cams_air_quality_data(date):
    c = cdsapi.Client()
    date_str = date.strftime('%Y-%m-%d')
    request = {
        "variable": CAMS_AIR_QUALITY_VARIABLES,
        "model": CAMS_AIR_QUALITY_MODEL,
        "date": [f"{date_str}/{date_str}"],
        "time": CAMS_AIR_QUALITY_TIMES,
        "leadtime_hour": CAMS_AIR_QUALITY_LEADTIME_HOUR,
        "type": CAMS_AIR_QUALITY_TYPE,
        "level": CAMS_AIR_QUALITY_LEVEL,
        "data_format": "netcdf_zip",  # Changed back to netcdf_zip format
        "area": CAMS_AIR_QUALITY_AREA
    }
    target_file = RAW_DIR / f"{date_str}_cams_air_quality.nc.zip"  # Changed file extension to match format
    print(f"Requesting CAMS Air Quality data for {date_str}...")
    c.retrieve(CAMS_AIR_QUALITY_DATASET, request, str(target_file))
    print(f"Saved CAMS Air Quality data to {target_file}")

def fetch_cams_atmos_composition_data(date):
    c = cdsapi.Client()
    date_str = date.strftime('%Y-%m-%d')

    # First, retrieve the surface pressure for Berlin
    surface_pressure_request = {
        "variable": ["surface_pressure"],
        "date": [f"{date_str}/{date_str}"],
        "time": CAMS_ATMOS_COMPOSITION_TIMES,
        "leadtime_hour": CAMS_ATMOS_COMPOSITION_LEADTIME_HOUR,
        "type": CAMS_ATMOS_COMPOSITION_TYPE,
        "data_format": "grib",
        "area": CAMS_ATMOS_COMPOSITION_AREA
    }
    surface_pressure_file = RAW_DIR / f"{date_str}_cams_surface_pressure.grib"
    print(f"Requesting CAMS Global surface pressure data for {date_str}...")
    c.retrieve(CAMS_ATMOS_COMPOSITION_DATASET, surface_pressure_request, str(surface_pressure_file))
    print(f"Saved CAMS Global surface pressure data to {surface_pressure_file}")

    # Open the surface pressure file and get the pressure value for Berlin
    ds = xr.open_dataset(surface_pressure_file, engine='cfgrib')
    # The surface pressure is in Pa, convert to hPa by dividing by 100
    surface_pressure = ds['sp'].isel(step=0).values[0, 0] / 100.0  # Convert from Pa to hPa
    ds.close()

    # Clean up temporary surface pressure files
    surface_pressure_file.unlink()  # Delete the .grib file
    idx_file = surface_pressure_file.with_suffix('.grib.5b7b6.idx')
    if idx_file.exists():
        idx_file.unlink()  # Delete the .idx file if it exists

    # Determine the appropriate pressure level to use
    # We want to use the pressure level closest to the surface pressure
    pressure_levels = [1000, 950, 925, 900, 850, 800, 700, 600, 500, 400, 300, 250, 200, 150, 100, 70, 50, 30, 20, 10, 7, 5, 3, 2, 1]
    closest_pressure_level = min(pressure_levels, key=lambda x: abs(x - surface_pressure))
    print(f"Using pressure level {closest_pressure_level} hPa (closest to surface pressure {surface_pressure:.2f} hPa)")

    # Now, retrieve the UVI data using the determined pressure level
    uvi_request = {
        "variable": CAMS_ATMOS_COMPOSITION_VARIABLE,
        "date": [f"{date_str}/{date_str}"],
        "time": CAMS_ATMOS_COMPOSITION_TIMES,
        "leadtime_hour": CAMS_ATMOS_COMPOSITION_LEADTIME_HOUR,
        "type": CAMS_ATMOS_COMPOSITION_TYPE,
        "pressure_level": [str(closest_pressure_level)],
        "data_format": "grib",
        "area": CAMS_ATMOS_COMPOSITION_AREA
    }
    uvi_file = RAW_DIR / f"{date_str}_cams_atmos_composition.grib"
    print(f"Requesting CAMS Atmospheric Composition data for {date_str}...")
    c.retrieve(CAMS_ATMOS_COMPOSITION_DATASET, uvi_request, str(uvi_file))
    print(f"Saved CAMS Atmospheric Composition data to {uvi_file}")

def main():
    today = datetime.utcnow().date()
    # Fetch today's forecast, which includes predictions for the next 4 days
    fetch_cams_air_quality_data(today)
    fetch_cams_atmos_composition_data(today)
    print("Successfully fetched CAMS forecast data!")

if __name__ == "__main__":
    main() 