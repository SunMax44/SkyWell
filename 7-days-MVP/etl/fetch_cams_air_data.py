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
import os

# Load .env for local development
load_dotenv()

RAW_DIR = Path(__file__).parent.parent / "raw/cams"

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
CAMS_AIR_QUALITY_LEADTIME_HOUR = [str(i) for i in range(0, 97)]  # 0 to 96 hours, hourly
CAMS_AIR_QUALITY_TYPE = ["forecast"]
CAMS_AIR_QUALITY_LEVEL = ["0"] # metres above surface
CAMS_AIR_QUALITY_AREA = [53, 13, 52, 14]  # North, West, South, East

# Ensure the URL and API token are provided through environment variables
def fetch_cams_air_quality_data(date):
    # Explicitly pass the URL and API key to avoid using .cdsapirc
    CAMS_API_URL = os.getenv("CAMS_API_URL", "https://ads.atmosphere.copernicus.eu/api")
    CAMS_API_KEY = os.getenv("CAMS_API_TOKEN")

    if not CAMS_API_KEY:
        raise ValueError("CAMS_API_TOKEN environment variable is required")
    
    # Initialize the cdsapi client with the correct URL and key from the environment
    c = cdsapi.Client(url=CAMS_API_URL, key=CAMS_API_KEY)
    
    date_str = date.strftime('%Y-%m-%d')
    request = {
        "variable": CAMS_AIR_QUALITY_VARIABLES,
        "model": CAMS_AIR_QUALITY_MODEL,
        "level": CAMS_AIR_QUALITY_LEVEL,
        "date": [f"{date_str}/{date_str}"],
        "type": CAMS_AIR_QUALITY_TYPE,
        "time": CAMS_AIR_QUALITY_TIMES,
        "leadtime_hour": CAMS_AIR_QUALITY_LEADTIME_HOUR,
        "data_format": "netcdf_zip",
        "area": CAMS_AIR_QUALITY_AREA
    }

    target_file = RAW_DIR / f"{date_str}_cams_air_quality.nc.zip"
    print(f"Requesting CAMS Air Quality data for {date_str}...")
    c.retrieve(CAMS_AIR_QUALITY_DATASET, request, str(target_file))
    print(f"Saved CAMS Air Quality data to {target_file}")

def main():
    today = datetime.utcnow().date()
    # Fetch today's forecast, which includes predictions for the next 4 days
    fetch_cams_air_quality_data(today)
    print("Successfully fetched CAMS forecast data!")

if __name__ == "__main__":
    main()