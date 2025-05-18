import xarray as xr
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple
import logging
from dataclasses import dataclass
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    uv_sensitivity: float  # 1-5 scale
    pollen_sensitivity: float  # 1-5 scale
    location: Tuple[float, float]  # (latitude, longitude)
    alert_threshold: float  # 1-10 scale
    notification_preferences: Dict[str, bool]  # e.g., {"email": True, "push": True}

class AlertProcessor:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.UV_MAX = 11
        self.POLLEN_MAX = 100
        
    def load_data(self) -> Tuple[xr.Dataset, xr.Dataset]:
        """Load UV and pollen data from NetCDF files."""
        try:
            uv_ds = xr.open_dataset(self.data_dir / "uv_berlin.nc")
            pollen_ds = xr.open_dataset(self.data_dir / "pollen_berlin.nc")
            return uv_ds, pollen_ds
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise

    def calculate_risk_score(self, 
                           uv_data: xr.DataArray, 
                           pollen_data: xr.DataArray,
                           user_profile: UserProfile) -> float:
        """Calculate personalized risk score based on user profile."""
        # Normalize the data
        uv_norm = uv_data / self.UV_MAX
        pollen_norm = pollen_data / self.POLLEN_MAX
        
        # Calculate weighted risk score
        risk_score = (
            uv_norm * user_profile.uv_sensitivity + 
            pollen_norm * user_profile.pollen_sensitivity
        ) / (user_profile.uv_sensitivity + user_profile.pollen_sensitivity) * 10
        
        return float(risk_score.clip(1, 10))

    def should_send_alert(self, risk_score: float, user_profile: UserProfile) -> bool:
        """Determine if an alert should be sent based on risk score and user threshold."""
        return risk_score >= user_profile.alert_threshold

    def generate_alert_message(self, risk_score: float, uv_value: float, pollen_value: float) -> str:
        """Generate a human-readable alert message."""
        severity = "High" if risk_score >= 8 else "Moderate" if risk_score >= 5 else "Low"
        
        message = f"⚠️ {severity} Risk Alert ⚠️\n\n"
        message += f"Current Risk Score: {risk_score:.1f}/10\n"
        message += f"UV Index: {uv_value:.1f}\n"
        message += f"Pollen Level: {pollen_value:.1f}\n\n"
        
        if risk_score >= 8:
            message += "Consider staying indoors or taking extra precautions."
        elif risk_score >= 5:
            message += "Take normal precautions for your activities."
        else:
            message += "Conditions are generally safe for your profile."
            
        return message

    def process_alerts(self, user_profile: UserProfile) -> List[Dict]:
        """Process data and generate alerts for a user."""
        try:
            uv_ds, pollen_ds = self.load_data()
            
            # Get the latest time step
            latest_time = uv_ds.time[-1]
            
            # Get data for user's location
            uv_data = uv_ds['uv_index'].sel(time=latest_time)
            pollen_data = sum([pollen_ds[var].sel(time=latest_time) 
                             for var in ['birch_pollen', 'grass_pollen', 'olive_pollen', 'ragweed_pollen']])
            
            # Calculate risk score
            risk_score = self.calculate_risk_score(uv_data, pollen_data, user_profile)
            
            alerts = []
            if self.should_send_alert(risk_score, user_profile):
                alert = {
                    "timestamp": datetime.now().isoformat(),
                    "risk_score": risk_score,
                    "uv_value": float(uv_data),
                    "pollen_value": float(pollen_data),
                    "message": self.generate_alert_message(risk_score, float(uv_data), float(pollen_data)),
                    "severity": "high" if risk_score >= 8 else "moderate" if risk_score >= 5 else "low"
                }
                alerts.append(alert)
                
                # Save alert to JSON file for the frontend
                self.save_alert(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error processing alerts: {e}")
            raise

    def save_alert(self, alert: Dict):
        """Save alert to a JSON file for the frontend to consume."""
        alerts_file = self.data_dir / "alerts.json"
        
        # Load existing alerts
        if alerts_file.exists():
            with open(alerts_file, 'r') as f:
                alerts = json.load(f)
        else:
            alerts = []
        
        # Add new alert
        alerts.append(alert)
        
        # Keep only last 10 alerts
        alerts = alerts[-10:]
        
        # Save updated alerts
        with open(alerts_file, 'w') as f:
            json.dump(alerts, f, indent=2)

def main():
    # Example usage
    processor = AlertProcessor()
    
    # Example user profile
    user_profile = UserProfile(
        uv_sensitivity=4.0,  # High UV sensitivity
        pollen_sensitivity=2.0,  # Moderate pollen sensitivity
        location=(52.5200, 13.4050),  # Berlin coordinates
        alert_threshold=5.0,  # Alert for moderate risk and above
        notification_preferences={"email": True, "push": True}
    )
    
    # Process alerts
    alerts = processor.process_alerts(user_profile)
    
    # Print alerts
    for alert in alerts:
        print(alert["message"])

if __name__ == "__main__":
    main() 