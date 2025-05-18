import cdsapi
from datetime import datetime, timedelta
import os

# Berlin bounding box: [North, West, South, East]
BERLIN_AREA = [53.5, 12.0, 51.5, 14.5]

# Date range: today + 7 days
start_date = datetime.now().strftime('%Y-%m-%d')
end_date = (datetime.now() + timedelta(days=6)).strftime('%Y-%m-%d')

os.makedirs('data', exist_ok=True)
c = cdsapi.Client()

# Fetch UV Index (CAMS global atmospheric composition forecasts)
print('Requesting UV index data...')
c.retrieve(
    'cams-global-atmospheric-composition-forecasts',
    {
        'date': f'{start_date}/{end_date}',
        'type': 'forecast',
        'format': 'netcdf',
        'variable': 'uv_index',
        'model_level': '60',
        'time': [
            '00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00',
        ],
        'area': BERLIN_AREA,
    },
    'data/uv_berlin.nc')
print('UV index data saved to data/uv_berlin.nc')

# Fetch Pollen (CAMS European air quality forecasts)
# Available pollen variables: birch, grass, olive, ragweed (as of 2024)
pollen_vars = [
    'birch_pollen',
    'grass_pollen',
    'olive_pollen',
    'ragweed_pollen',
]
print('Requesting pollen data...')
c.retrieve(
    'cams-europe-air-quality-forecasts',
    {
        'date': f'{start_date}/{end_date}',
        'type': 'forecast',
        'format': 'netcdf',
        'variable': pollen_vars,
        'model_level': '0',
        'time': [
            '00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00',
        ],
        'area': BERLIN_AREA,
    },
    'data/pollen_berlin.nc')
print('Pollen data saved to data/pollen_berlin.nc') 