# Copernicus Data Pipeline for Pollen and UV Data

This project implements a data pipeline for extracting real-time pollen and UV data from Copernicus satellite data, with a focus on the Berlin area.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Copernicus Climate Data Store (CDS) API:
   - Register at https://cds.climate.copernicus.eu/
   - Create an API key
   - Create a file `~/.cdsapirc` with your API key:
   ```
   url: https://cds.climate.copernicus.eu/api/v2
   key: YOUR-API-KEY
   ```

## Usage

Run the data pipeline:
```bash
python data_pipeline.py
```

The script will:
1. Fetch UV and pollen data for Berlin
2. Process the data
3. Save the results in the `data` directory

## Notes

- The current implementation focuses on Berlin (coordinates: 52.5200°N, 13.4050°E)
- The data pipeline is set up to fetch both real-time and forecast data
- The processed data is saved in CSV format for easy access

## Next Steps

1. Implement proper data processing based on actual Copernicus dataset structure
2. Add visualization capabilities
3. Implement forecast model if needed
4. Extend to cover all of Europe 