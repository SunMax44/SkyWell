from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import sys
sys.path.append(str(Path(__file__).parent.parent))
from core import risk, advice
from api.cache import cache

app = FastAPI()

# Set up Jinja2 environment
TEMPLATE_DIR = Path(__file__).parent.parent / "chatbot/templates"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

@app.get("/risk")
@cache(ttl=60)
def get_risk(profile: Optional[str] = Query(None), date: Optional[str] = Query(None)):
    import datetime
    date_str = date or datetime.date.today().strftime("%Y-%m-%d")
    try:
        env_data = risk.load_environmental_data(date_str)
        profile_enum = risk.HealthProfile[profile] if profile else risk.HealthProfile.HEALTHY_ADULT
        assessment = risk.calculate_profile_risk(profile=profile_enum, environmental_data=env_data)
        return JSONResponse({
            "profile": profile_enum.value,
            "date": date_str,
            "risk_vector": assessment.sub_scores,
            "final_score": assessment.final_score,
            "top_contributor": assessment.top_contributor[0].value if assessment.top_contributor else None
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/chat")
@cache(ttl=60)
def get_chat(profile: Optional[str] = Query(None), date: Optional[str] = Query(None)):
    import datetime
    date_str = date or datetime.date.today().strftime("%Y-%m-%d")
    try:
        env_data = risk.load_environmental_data(date_str)
        profile_enum = risk.HealthProfile[profile] if profile else risk.HealthProfile.HEALTHY_ADULT
        assessment = risk.calculate_profile_risk(profile=profile_enum, environmental_data=env_data)
        advice_text = advice.choose_advice(profile_enum, assessment)
        template = jinja_env.get_template("advice.txt")
        rendered = template.render(
            profile=profile_enum.value,
            date=date_str,
            risk=assessment.top_contributor[0].value if assessment.top_contributor else None,
            advice=advice_text
        )
        return PlainTextResponse(rendered)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500) 