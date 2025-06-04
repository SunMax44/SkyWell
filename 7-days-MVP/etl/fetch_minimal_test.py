import cdsapi
from datetime import datetime

client = cdsapi.Client()

dataset = "cams-global-atmospheric-composition-forecasts"
request = {
    "variable": ["ozone"],
    "date": datetime.utcnow().strftime("%Y-%m-%d"),
    "time": ["00:00"],
    "format": "netcdf",
    "type": "forecast",
    "model_level": "60",
    "area": [90, -180, -90, 180],
}

target = "raw/minimal_test_global_cams.nc"

client.retrieve(dataset, request, target) 