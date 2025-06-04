# SkyWell - Personalized Environmental Risk Advisor

A data-focused MVP app that provides personalized environmental risk scores and recommendations based on user health profiles.

## Project Structure

```
skywell/
├── etl/                → Data fetching scripts
├── core/               → Core processing logic
├── api/                → FastAPI backend
├── chatbot/            → Chat templates
├── ui/                 → Streamlit frontend
├── raw/                → Raw input files
├── data/               → Processed data files
├── tests/              → Test files
└── .github/workflows/  → CI/CD workflows
```

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Create a .env file with:
CAMS_API_TOKEN=your_token_here
```

## Day 1 - Data Access

The first step is to fetch CAMS data for Berlin. This script downloads today's and 3-day forecast data for air quality and pollen.

To run the data fetcher:
```bash
python etl/fetch.py
```

Note: You'll need to manually download a Sentinel-3 UV GeoTIFF file for now. The GEE export functionality will be implemented in a future sprint.

## Development Status

This is a 7-day MVP project. Current status: Day 1 - Data Access

## License

[Your License Here] 