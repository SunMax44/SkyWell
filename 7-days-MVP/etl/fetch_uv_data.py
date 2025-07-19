#!/usr/bin/env python3
"""
UV index data fetching from Open-Meteo API.
This module provides functions to fetch current and forecast UV index data for Berlin.
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json
import os
import time
import xarray as xr
from typing import Optional, List, Tuple
import rioxarray  # Add this import at the top

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://api.open-meteo.com/v1/forecast"
DATA_DIR = Path("data/uv")
RATE_LIMIT_DELAY = 1.0  # Delay between requests in seconds
MAX_RETRIES = 3  # Maximum number of retries for failed requests

# Berlin bounding box (matching grid.py)
BERLIN_BOUNDS = {
    'north': 52.75,
    'south': 52.25,
    'east': 13.85,
    'west': 13.05
}

# Grid resolution for UV (now 0.1° to match CAMS)
UV_GRID_RESOLUTION = 0.1  # degrees

def ensure_data_dir():
    """Ensure the data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def fetch_uv_forecast(lat, lon):
    """
    Fetch UV forecast data for a specific location.
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        
    Returns:
        dict: Response data from the API
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "uv_index",
        "forecast_days": 4,
        "timezone": "auto"
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Too Many Requests
                wait_time = (attempt + 1) * RATE_LIMIT_DELAY * 2  # Exponential backoff
                logger.warning(f"Rate limit hit, waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"Error fetching UV forecast for lat={lat}, lon={lon}: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Error fetching UV forecast for lat={lat}, lon={lon}: {str(e)}")
            raise

def process_forecast_data(data, lat, lon):
    """
    Process the forecast data into a DataFrame.
    
    Args:
        data (dict): Raw forecast data from the API
        lat (float): Latitude
        lon (float): Longitude
        
    Returns:
        pd.DataFrame: Processed forecast data
    """
    df = pd.DataFrame({
        'time': data['hourly']['time'],
        'uv_index': data['hourly']['uv_index']
    })
    
    df['latitude'] = lat
    df['longitude'] = lon
    df['time'] = pd.to_datetime(df['time'])
    
    return df

def get_grid_points():
    """
    Generate grid points for Berlin area at 0.1° resolution.
    Returns:
        list: List of (lat, lon) tuples
    """
    lats = np.arange(BERLIN_BOUNDS['south'], BERLIN_BOUNDS['north'] + UV_GRID_RESOLUTION, UV_GRID_RESOLUTION)
    lons = np.arange(BERLIN_BOUNDS['west'], BERLIN_BOUNDS['east'] + UV_GRID_RESOLUTION, UV_GRID_RESOLUTION)
    return [(lat, lon) for lat in lats for lon in lons]

def fetch_uv_forecast_grid():
    """
    Fetch UV forecast data for all grid points.
    
    Returns:
        pd.DataFrame: Combined forecast data for all grid points
    """
    grid_points = get_grid_points()
    all_data = []
    total_points = len(grid_points)
    
    for i, (lat, lon) in enumerate(grid_points, 1):
        try:
            logger.info(f"Fetching UV data for lat={lat}, lon={lon} ({i}/{total_points})")
            data = fetch_uv_forecast(lat, lon)
            df = process_forecast_data(data, lat, lon)
            all_data.append(df)
            time.sleep(RATE_LIMIT_DELAY)  # Add delay between requests
        except Exception as e:
            logger.error(f"Error processing data for lat={lat}, lon={lon}: {str(e)}")
            continue
    
    if not all_data:
        raise ValueError("No data was successfully fetched")
    
    return pd.concat(all_data, ignore_index=True)

def save_forecast(df):
    """
    Save the forecast data to a CSV file.
    
    Args:
        df (pd.DataFrame): Forecast data to save
    """
    ensure_data_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = DATA_DIR / f"uv_forecast_{timestamp}.csv"
    df.to_csv(filename, index=False)
    logger.info(f"Saved forecast data to {filename}")

def save_forecast_tif(df):
    """
    Save the forecast data as a GeoTIFF file compatible with the grid system.
    
    Args:
        df (pd.DataFrame): Forecast data to save
    """
    # Get the current date for filename
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Create a pivot table to get UV values for each lat/lon
    # Use the first time step for now (current UV index)
    current_data = df[df['time'] == df['time'].min()].copy()
    
    if current_data.empty:
        raise ValueError("No current UV data available")
    
    # Create a 2D grid
    lats = sorted(current_data['latitude'].unique())
    lons = sorted(current_data['longitude'].unique())
    
    # Create a 2D array
    uv_grid = np.zeros((len(lats), len(lons)))
    
    for i, lat in enumerate(lats):
        for j, lon in enumerate(lons):
            mask = (current_data['latitude'] == lat) & (current_data['longitude'] == lon)
            if mask.any():
                uv_grid[i, j] = current_data.loc[mask, 'uv_index'].iloc[0]
    
    # Create xarray DataArray
    da = xr.DataArray(
        uv_grid,
        coords={'latitude': lats, 'longitude': lons},
        dims=['latitude', 'longitude'],
        name='uv_index'
    )
    
    # Set CRS using rioxarray
    da = da.rio.write_crs("EPSG:4326")
    
    # Save as GeoTIFF in the main data directory
    output_path = Path("data") / f"{current_date}_uv_index.tif"
    output_path.parent.mkdir(exist_ok=True)
    
    da.rio.to_raster(
        output_path,
        driver='COG',
        compress='LZW'
    )
    
    logger.info(f"Saved UV data as GeoTIFF to {output_path}")

def get_latest_forecast():
    """
    Get the latest UV forecast data and save it.
    
    Returns:
        pd.DataFrame: The latest forecast data
    """
    try:
        df = fetch_uv_forecast_grid()
        save_forecast(df)
        save_forecast_tif(df)  # Also save as GeoTIFF
        return df
    except Exception as e:
        logger.error(f"Error getting latest forecast: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        forecast = get_latest_forecast()
        print("\nUV Index Forecast for Berlin:")
        print(f"Data shape: {forecast.shape}")
        print(f"Time range: {forecast['time'].min()} to {forecast['time'].max()}")
        print(f"Latitude range: {forecast['latitude'].min()} to {forecast['latitude'].max()}")
        print(f"Longitude range: {forecast['longitude'].min()} to {forecast['longitude'].max()}")
        print(f"UV Index range: {forecast['uv_index'].min()} to {forecast['uv_index'].max()}")
    except Exception as e:
        logger.error(f"Failed to fetch UV forecast: {str(e)}")
        raise 