import xarray as xr
from pathlib import Path
from datetime import datetime

# List of variable names (matching your filenames)
variables = [
    "pm2p5_conc", "pm10_conc", "o3_conc", "no2_conc", "so2_conc",
    "uv_biologically_effective_dose",
    "bpg_conc", "gpg_conc", "opg_conc", "mpg_conc",
    "rwpg_conc", "apg_conc"
]

date = datetime.utcnow().strftime("%Y-%m-%d")
data_dir = Path("7-days-MVP/data")

for var in variables:
    file_path = data_dir / f"{date}_{var}.tif"
    print(f"\n--- {var} ---")
    if not file_path.exists():
        print(f"File not found: {file_path}")
        continue
    try:
        da = xr.open_dataarray(file_path)
        print(f"Shape: {da.shape}")
        print(f"Dimensions: {da.dims}")
        print(f"Coordinates: {list(da.coords)}")
        # Print band values if present
        if "band" in da.coords:
            print(f"Band values: {da['band'].values}")
        # Print a small sample of the data
        print("Sample data:", da.values.ravel()[:5])
    except Exception as e:
        print(f"Error loading {file_path}: {e}") 