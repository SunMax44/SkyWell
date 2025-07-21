import gradio as gr
import requests
import datetime

API_URL = "http://localhost:8000"

# Fetch available health profiles from the backend or hardcode for MVP
def get_health_profiles():
    # For MVP, hardcode common profiles
    return [
        "HEALTHY_ADULT",
        "ASTHMA",
        "COPD",
        "CARDIAC",
        "DIABETES",
        "ECZEMA",
        "ALLERGIC_RHINITIS",
        "IMMUNOCOMPROMISED"
    ]

def fetch_risk(profile, date):
    try:
        resp = requests.get(f"{API_URL}/risk", params={"profile": profile, "date": date})
        resp.raise_for_status()
        data = resp.json()
        risk_vector = data.get("risk_vector", [])
        final_score = data.get("final_score", None)
        top_contributor = data.get("top_contributor", None)
        return risk_vector, final_score, top_contributor, ""
    except Exception as e:
        return [], None, None, f"Error: {e}"

def fetch_advice(profile, date):
    try:
        resp = requests.get(f"{API_URL}/chat", params={"profile": profile, "date": date})
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        return f"Error: {e}"

def main(profile, date):
    risk_vector, final_score, top_contributor, risk_error = fetch_risk(profile, date)
    advice = fetch_advice(profile, date)
    return (
        str(risk_vector),
        str(final_score),
        str(top_contributor),
        advice,
        risk_error
    )

with gr.Blocks() as demo:
    gr.Markdown("# SkyWell: Personalized Environmental Risk Advisor")
    with gr.Row():
        profile = gr.Dropdown(get_health_profiles(), label="Health Profile", value="HEALTHY_ADULT")
        date = gr.Textbox(label="Date (YYYY-MM-DD)", value=datetime.date.today().strftime("%Y-%m-%d"))
    with gr.Row():
        risk_vector = gr.Textbox(label="Risk Vector")
        final_score = gr.Textbox(label="Final Score")
        top_contributor = gr.Textbox(label="Top Contributor")
    advice = gr.Textbox(label="Advice", lines=3)
    risk_error = gr.Textbox(label="Error", lines=1)
    btn = gr.Button("Get Risk & Advice")
    btn.click(main, inputs=[profile, date], outputs=[risk_vector, final_score, top_contributor, advice, risk_error])

demo.launch() 