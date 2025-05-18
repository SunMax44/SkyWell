import streamlit as st

# Claudia-specific thresholds and weights
CLAUDIA_THRESHOLDS = {
    'PM2.5': [(8, 2), (20, 0), (float('inf'), -2)],
    'PM10': [(15, 2), (35, 0), (float('inf'), -2)],
    'O3': [(20, 2), (60, 0), (float('inf'), -2)],
    'NO2': [(15, 2), (40, 0), (float('inf'), -2)],
    'SO2': [(2, 2), (6, 0), (float('inf'), -2)],
    'Pollen': [(50, 2), (150, 0), (float('inf'), -2)],
    'Mold': [(500, 2), (3000, 0), (float('inf'), -2)],
    'UV': [(2, 2), (4, 0), (6, -1), (float('inf'), -2)],
    'Sunshine': [(1800, 2), (2500, 0), (float('inf'), -2)],
    'Humidity': [(40, -2), (50, 2), (65, 0), (float('inf'), -2)],
    'Temperature': [(14, 0), (18, 2), (25, 0), (float('inf'), -2)],
    'Pressure': [(1010, 0), (1020, 2), (1030, 1), (float('inf'), -2)],
}

CLAUDIA_WEIGHTS = {
    'PM2.5': 2,
    'PM10': 2,
    'O3': 2,
    'NO2': 2,
    'SO2': 1,
    'Pollen': 1,
    'Mold': 3,
    'UV': 3,
    'Sunshine': 2,
    'Humidity': 4,
    'Temperature': 2,
    'Pressure': 3,
}

# Risk scoring logic
def get_score(value, thresholds):
    for limit, score in thresholds:
        if value <= limit:
            return score
    return thresholds[-1][1]

def compute_risk(inputs):
    total = 0
    max_score = 0
    for factor, value in inputs.items():
        score = get_score(value, CLAUDIA_THRESHOLDS[factor])
        weight = CLAUDIA_WEIGHTS.get(factor, 1)
        total += score * weight
        max_score += 2 * weight  # Max score per factor (if score is 2)
    risk_score = 10 - ((total / max_score) * 10)
    return round(min(max(risk_score, 0), 10), 2)

# Streamlit config
st.set_page_config(page_title="Claudia's Health Risk Evaluator", layout="centered")

# Sidebar controls
with st.sidebar:
    st.markdown("### ℹ️ Instructions")
    st.markdown("Adjust environmental values below to estimate Claudia’s health risk.")
    st.markdown("**Score Range:** 0 = Low Risk, 10 = High Risk")
    st.markdown("### 🧪 Environmental Inputs")

    inputs = {
        'PM2.5': st.slider("PM2.5 (µg/m³)", 0, 100, 12),
        'PM10': st.slider("PM10 (µg/m³)", 0, 100, 20),
        'O3': st.slider("Ozone O₃ (ppb)", 0, 120, 25),
        'NO2': st.slider("NO₂ (ppb)", 0, 100, 18),
        'SO2': st.slider("SO₂ (ppb)", 0, 50, 3),
        'Pollen': st.slider("Pollen Count (grains/m³)", 0, 500, 75),
        'Mold': st.slider("Mold Spores (spores/m³)", 0, 20000, 2500),
        'UV': st.slider("UV Index", 0, 12, 5),
        'Sunshine': st.slider("Sunshine Hours/year", 0, 4000, 2200),
        'Humidity': st.slider("Humidity (%)", 0, 100, 55),
        'Temperature': st.slider("Avg Temperature (°C)", -10, 40, 20),
        'Pressure': st.slider("Barometric Pressure (hPa)", 950, 1050, 1015),
    }

# Main content
st.title("🌿 Claudia's Unique Health Risk Evaluator")

st.markdown("### 🧬 Claudia’s Health Profile")
st.dataframe({
    "Health Condition": [
        "Sun Sensitivity", "Skin Disease", "Arthritis", "Respiratory Condition",
        "Pollen Allergy", "Mold/Mite Allergy", "Medicines"
    ],
    "Sensitivity Level": [
        "Medium", "High", "Medium", "Low", "Low", "Low", "Medium"
    ],
    "Condition": [
        "Photosensitivity", "Psoriasis", "Possible", "-", "-", "-", "Yes"
    ],
    "Related Environmental Factor(s)": [
        "UV Index, Sunshine", "Humidity, UV, Temp", "Pressure, Humidity, Temp",
        "PM2.5, PM10, O₃, NO₂, SO₂", "Pollen Count", "Mold, Humidity", "UV exposure"
    ],
    "Weight": [3, 4, 2, 2, 1, 1, 1]
})

# Compute score
risk_score = compute_risk(inputs)

st.metric(label="🩺 Claudia’s Risk Score", value=f"{risk_score} / 10")

# Result interpretation
if risk_score <= 3:
    st.success("✅ Low Risk – This environment is generally safe for Claudia.")
elif risk_score <= 6:
    st.warning("⚠️ Moderate Risk – Some environmental factors may need monitoring.")
else:
    st.error("🚨 High Risk – This environment may negatively impact Claudia’s health.")
