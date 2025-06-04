#!/usr/bin/env python3
"""
Fetch CAMS air quality and pollen data for Berlin and save to raw/ directory.
This script downloads 4-day forecast data as NetCDF for selected variables and times.
"""

import cdsapi
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load .env for local development
load_dotenv()

RAW_DIR = Path(__file__).parent.parent / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

DATASET = "cams-europe-air-quality-forecasts"
VARIABLES = [
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
MODEL = ["ensemble"]
LEVEL = ["0"]
TYPE = ["forecast"]
TIMES = ["00:00"]
LEADTIME_HOUR = [
    "0", "8", "12", "16", "20",
    "24", "32", "36", "40", "44",
    "48", "56", "60", "64", "68",
    "72", "80", "84", "88", "92", "96"
]
AREA = [53, 13, 52.3, 14]  # North, West, South, East (Berlin)


def fetch_cams_data(date):
    c = cdsapi.Client()
    date_str = date.strftime('%Y-%m-%d')
    request = {
        "variable": VARIABLES,
        "model": MODEL,
        "level": LEVEL,
        "date": [f"{date_str}/{date_str}"],
        "type": TYPE,
        "time": TIMES,
        "leadtime_hour": LEADTIME_HOUR,
        "data_format": "netcdf_zip",
        "area": AREA
    }
    target_file = RAW_DIR / f"{date_str}_cams.nc.zip"
    print(f"Requesting CAMS data for {date_str}...")
    c.retrieve(DATASET, request, str(target_file))
    print(f"Saved CAMS data to {target_file}")


def main():
    today = datetime.utcnow().date()
    for i in range(4):
        fetch_cams_data(today + timedelta(days=i))
    print("Successfully fetched all CAMS data!")

if __name__ == "__main__":
    main() 