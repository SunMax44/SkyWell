import folium
from folium import plugins
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import branca.colormap as cm

# Berlin coordinates
BERLIN_LAT = 52.5200
BERLIN_LON = 13.4050

GRID_SIZE = 20  # number of grid cells per axis

# User weights for risk calculation
UV_WEIGHT = 4  # strong sensitivity
POLLEN_WEIGHT = 2  # slight allergy

# Normalization constants
UV_MAX = 11
POLLEN_MAX = 100


def generate_mock_data():
    """Generate mock data for demonstration purposes."""
    lat_range = np.linspace(BERLIN_LAT - 1, BERLIN_LAT + 1, GRID_SIZE)
    lon_range = np.linspace(BERLIN_LON - 1, BERLIN_LON + 1, GRID_SIZE)
    base_date = datetime.now()
    timestamps = [base_date + timedelta(days=i) for i in range(7)]
    data = []
    for timestamp in timestamps:
        for i, lat in enumerate(lat_range[:-1]):
            for j, lon in enumerate(lon_range[:-1]):
                uv_index = np.random.normal(5, 2)
                uv_index = max(0, min(UV_MAX, uv_index))
                pollen = np.random.normal(50, 20)
                pollen = max(0, min(POLLEN_MAX, pollen))
                # Normalize
                uv_norm = uv_index / UV_MAX
                pollen_norm = pollen / POLLEN_MAX
                # Risk score calculation
                risk_score = (uv_norm * UV_WEIGHT + pollen_norm * POLLEN_WEIGHT) / (UV_WEIGHT + POLLEN_WEIGHT) * 10
                risk_score = max(1, min(10, risk_score))
                data.append({
                    'timestamp': timestamp,
                    'lat1': lat,
                    'lat2': lat_range[i+1],
                    'lon1': lon,
                    'lon2': lon_range[j+1],
                    'uv_index': uv_index,
                    'pollen_concentration': pollen,
                    'risk_score': risk_score
                })
    return pd.DataFrame(data)

def add_rectangles_for_risk(m, df):
    for timestamp in df['timestamp'].unique():
        timestamp_str = timestamp.strftime('%Y-%m-%d')
        fg = folium.FeatureGroup(name=f"Risk Score {timestamp_str}", show=(timestamp==df['timestamp'].unique()[0]))
        day_data = df[df['timestamp'] == timestamp]
        for _, row in day_data.iterrows():
            color = cm.LinearColormap(['green', 'yellow', 'orange', 'red', 'purple'], vmin=1, vmax=10)(row['risk_score'])
            bounds = [
                [row['lat1'], row['lon1']],
                [row['lat2'], row['lon2']]
            ]
            popup_html = f"""
            <b>Risk Score:</b> {row['risk_score']:.2f} (1-10)<br>
            <b>UV Index:</b> {row['uv_index']:.2f} (0-11)<br>
            <b>Pollen:</b> {row['pollen_concentration']:.2f} (0-100)<br>
            <b>UV Weight:</b> {UV_WEIGHT}<br>
            <b>Pollen Weight:</b> {POLLEN_WEIGHT}<br>
            <b>Location:</b> Lat {row['lat1']:.3f}, Lon {row['lon1']:.3f}
            """
            folium.Rectangle(
                bounds=bounds,
                color=None,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(fg)
        fg.add_to(m)

def create_interactive_map():
    df = generate_mock_data()
    m = folium.Map(location=[BERLIN_LAT, BERLIN_LON], zoom_start=10, tiles='CartoDB positron')
    risk_colormap = cm.LinearColormap(
        colors=['green', 'yellow', 'orange', 'red', 'purple'],
        vmin=1, vmax=10,
        caption='Risk Score (1-10)'
    )
    risk_colormap.add_to(m)
    add_rectangles_for_risk(m, df)
    folium.LayerControl(collapsed=False).add_to(m)
    m.save('data/interactive_map.html')
    print("Interactive map has been created at data/interactive_map.html")

if __name__ == "__main__":
    create_interactive_map() 