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

## Data Sources & Grid Resolution

- **Air Quality & Pollen:** Fetched from CAMS at 0.1° resolution, then interpolated to a 0.01° grid for harmonization and risk scoring.
- **UV Index:** Fetched from Open-Meteo at 0.1° resolution, then interpolated to a 0.01° grid.
- All harmonized data is saved as COG GeoTIFFs in the `data/` directory.

## Customizable Risk Profiles

- The backend now supports user-defined/customizable risk profiles: users can select which environmental variables matter to them and assign custom weights.
- This is in addition to the predefined health profiles (e.g., asthma, COPD, etc.).

## Day 1 - Data Access

The first step is to fetch CAMS data for Berlin. This script downloads today's and 3-day forecast data for air quality and pollen.

To run the data fetcher:
```bash
python etl/fetch.py
```

Note: You'll need to manually download a Sentinel-3 UV GeoTIFF file for now. The GEE export functionality will be implemented in a future sprint.

## Risk Thresholds & Scientific Sources

The SAFE and DANGER anchor values (e.g., PM₂.₅ 15–75 µg/m³, PM₁₀ 45–150 µg/m³, etc.) used for risk normalization are based on the latest evidence-based, public-health-adopted guidelines:

- **🏥 WHO (2021) – Global Air Quality Guidelines**
  - World Health Organization. WHO Global Air Quality Guidelines: Particulate Matter (PM₂.₅ and PM₁₀), Ozone, Nitrogen Dioxide, Sulfur Dioxide and Carbon Monoxide. Geneva: WHO, 22 September 2021.
  - [WHO AQG Summary](https://www.who.int/publications/i/item/9789240034228)
- **🇪🇺 European Air Quality Index (EAQI) Bands**
  - European Environment Agency. “European Air Quality Index (EAQI) — Definition of bands for PM₂.₅, PM₁₀, NO₂, O₃, SO₂.” EEA Air Index, 4 July 2025. [airindex.eea.europa.eu](https://airindex.eea.europa.eu/)
- **WHO AQG and Evidence-Based Thresholds**
  - World Health Organization. “WHO Air Quality Guidelines—Aiming for Healthier Air for All.” International Journal of Public Health, vol. 66, Sep 2021.
- **Revised Short-Term WHO Guidelines**
  - Xue‑yan Zheng, Pablo Orellano, et al. “Updated World Health Organization Air Quality Guidelines: Short‑term Exposure Levels.” Environmental Science & Technology Letters 9, no. 6 (6 June 2022).
- **Additional references:**
  - Wikipedia, ww2.arb.ca.gov, arXiv, Eionet Portal, MDPI, SSPH+, IQAir Newsroom, PMC, pubs.acs.org

These references ensure the risk‑scoring model aligns with the latest clinically meaningful, evidence-based, and public-health-adopted thresholds for air quality and environmental health.

## Development Status

This is a 7-day MVP project. Current status: Day 1 - Data Access

## License

[Your License Here] 