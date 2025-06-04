#!/usr/bin/env python3
"""
Fetch CAMS air quality, pollen, and UVI data and save to raw/ directory.
This script downloads forecast data as NetCDF and GRIB for selected variables and times.
"""

import cdsapi
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load .env for local development
load_dotenv()

RAW_DIR = Path(__file__).parent.parent / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# CAMS Europe Air Quality Forecasts parameters
CAMS_EUROPE_DATASET = "cams-europe-air-quality-forecasts"
CAMS_EUROPE_VARIABLES = [
    "alder_pollen",
    "birch_pollen",
    "grass_pollen",
    "mugwort_pollen",
    "nitrogen_dioxide",
    "ozone",
    "particulate_matter_2.5um",
    "particulate_matter_10um",
    "ragweed_pollen",
    "sulphur_dioxide"
]
CAMS_EUROPE_MODEL = ["ensemble"]
CAMS_EUROPE_LEVEL = ["0"]
CAMS_EUROPE_TYPE = ["forecast"]
CAMS_EUROPE_TIMES = ["00:00"]
CAMS_EUROPE_LEADTIME_HOUR = [
    "0", "8", "12", "16", "20",
    "24", "32", "36", "40", "44",
    "48", "56", "60", "64", "68",
    "72", "80", "84", "88", "92", "96"
]
CAMS_EUROPE_AREA = [53, 13, 52.3, 14]  # North, West, South, East (Berlin)

# CAMS Global Atmospheric Composition Forecasts parameters (for UVI)
CAMS_GLOBAL_DATASET = "cams-global-atmospheric-composition-forecasts"
CAMS_GLOBAL_VARIABLE = ["uv_biologically_effective_dose"]
CAMS_GLOBAL_TYPE = ["forecast"]
CAMS_GLOBAL_TIMES = ["00:00"]
# Adjust lead times to match CAMS Europe for consistency
CAMS_GLOBAL_LEADTIME_HOUR = [
    "0", "8", "12", "16", "20",
    "24", "32", "36", "40", "44",
    "48", "56", "60", "64", "68",
    "72", "80", "84", "88", "92", "96"
]
CAMS_GLOBAL_AREA = [53, 13, 52, 14] # Slightly different area definition in global dataset

def fetch_cams_europe_data(date):
    c = cdsapi.Client()
    date_str = date.strftime('%Y-%m-%d')
    request = {
        "variable": CAMS_EUROPE_VARIABLES,
        "model": CAMS_EUROPE_MODEL,
        "level": CAMS_EUROPE_LEVEL,
        "date": [f"{date_str}/{date_str}"],
        "type": CAMS_EUROPE_TYPE,
        "time": CAMS_EUROPE_TIMES,
        "leadtime_hour": CAMS_EUROPE_LEADTIME_HOUR,
        "data_format": "netcdf_zip",
        "area": CAMS_EUROPE_AREA
    }
    target_file = RAW_DIR / f"{date_str}_cams.nc.zip"
    print(f"Requesting CAMS Europe data for {date_str}...")
    c.retrieve(CAMS_EUROPE_DATASET, request, str(target_file))
    print(f"Saved CAMS Europe data to {target_file}")

def fetch_cams_global_uvi_data(date):
    c = cdsapi.Client()
    date_str = date.strftime('%Y-%m-%d')
    request = {
        "variable": CAMS_GLOBAL_VARIABLE,
        "date": [f"{date_str}/{date_str}"],
        "time": CAMS_GLOBAL_TIMES,
        "leadtime_hour": CAMS_GLOBAL_LEADTIME_HOUR,
        "type": CAMS_GLOBAL_TYPE,
        "data_format": "grib", # Requesting GRIB format
        "area": CAMS_GLOBAL_AREA
    }
    target_file = RAW_DIR / f"{date_str}_cams_uvi.grib" # Save as .grib
    print(f"Requesting CAMS Global UVI data for {date_str}...")
    c.retrieve(CAMS_GLOBAL_DATASET, request, str(target_file))
    print(f"Saved CAMS Global UVI data to {target_file}")

def main():
    today = datetime.utcnow().date()
    # Only fetch today's forecast, which includes predictions for the next 4 days
    fetch_cams_europe_data(today)
    fetch_cams_global_uvi_data(today)
    print("Successfully fetched CAMS forecast data!")

if __name__ == "__main__":
    main() 