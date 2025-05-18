# SkyWell

![Project Logo](data/images/logo.jpeg)

This project is a smart, AI-powered pipeline that processes satellite weather data and personal user information to deliver **personalized weather alerts**. Whether it’s high pollen count or a stormy afternoon, our system ensures that users receive timely, tailored forecasts based on both environmental data and their specific sensitivities or preferences.

## 🔍 Overview

We combine **satellite data** with **user-specific health profiles** to create a system that goes beyond generic forecasts. The goal is to prevent avoidable exposure to weather-related health triggers, such as:
- High pollen levels for allergy sufferers
- Sudden temperature changes for chronic disease patients
- Air quality warnings for sensitive individuals

## 🔧 How It Works

1. **Data Collection**  
   Satellite and environmental data are continuously collected (e.g., temperature, pollen count, air pressure).

2. **Data Processing**  
   Raw data is filtered and structured using a preprocessing pipeline.

3. **User Input**  
   Users input personal health information such as allergies, chronic diseases, or preferences.

4. **AI Modeling**  
   An AI model processes both environmental data and user profiles to predict personalized impacts.

5. **Forecast Display**  
   General forecasts are displayed on users' mobile devices.

6. **Personalized Alerts**  
   If the AI model identifies any risk based on the user's profile, a tailored notification is sent to their mobile device.

---

## 🧠 Architecture Diagram

![Pipeline Diagram](data/images/pipeline.png)


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
