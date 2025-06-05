#!/usr/bin/env python3
"""
Risk scoring module for SkyWell.

This module provides functions to normalize input variables and compute a risk vector
based on user health profiles.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import xarray as xr
from pathlib import Path
import math
from datetime import datetime, timedelta
import logging
from typing_extensions import TypedDict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthProfile(Enum):
    """Enumeration of all supported health profiles."""
    HEALTHY_ADULT = "Healthy adult (general overview)"
    ASTHMA_CHILD = "Child with asthma (high risk)"
    SEASONAL_ALLERGIC_RHINITIS = "Seasonal allergic rhinitis (hay-fever)"
    ALLERGIC_ASTHMA = "Allergic (extrinsic) asthma"
    COPD = "Chronic Obstructive Pulmonary Disease (COPD)"
    ISCHAEMIC_HEART_DISEASE = "Ischaemic heart disease / heart-failure"
    TYPE2_DIABETES = "Type-2 diabetes with cardio-metabolic risk"
    PREGNANCY = "Pregnancy (pre-eclampsia / pre-term risk)"
    SKIN_CANCER_SURVIVOR = "Skin-cancer survivors & high-UV phenotypes (Fitzpatrick I–II)"
    VITILIGO = "Vitiligo / albinism (pigment-loss disorders)"
    LUPUS = "Systemic lupus erythematosus (photosensitive)"
    ALLERGIC_CONJUNCTIVITIS = "Allergic conjunctivitis & other ocular allergies"
    ATOPIC_DERMATITIS = "Atopic dermatitis (eczema)"

class EnvironmentalVariable(Enum):
    """Enumeration of all environmental variables we track."""
    BIRCH_POLLEN = "birch_pollen"
    GRASS_POLLEN = "grass_pollen"
    OLIVE_POLLEN = "olive_pollen"
    MUGWORT_POLLEN = "mugwort_pollen"
    RAGWEED_POLLEN = "ragweed_pollen"
    ALDER_POLLEN = "alder_pollen"
    PM2P5 = "pm2p5_conc"
    PM10 = "pm10_conc"
    OZONE = "o3_conc"
    NO2 = "no2_conc"
    SO2 = "so2_conc"
    UV = "uv_biologically_effective_dose"

class ThresholdConfig(TypedDict):
    """Type definition for threshold configuration."""
    safe: float
    danger: float
    unit: str
    window: str

class VariableTimingConfig(TypedDict):
    """Type definition for variable timing configuration."""
    window: str
    alert_threshold: float
    relevant_profiles: List[HealthProfile]

@dataclass
class HealthProfileConfig:
    """Configuration for a health profile including its weights for different environmental variables."""
    name: HealthProfile
    weights: Dict[EnvironmentalVariable, float]
    description: str

# Define the health profile configurations
HEALTH_PROFILES = {
    HealthProfile.HEALTHY_ADULT: HealthProfileConfig(
        name=HealthProfile.HEALTHY_ADULT,
        weights={
            EnvironmentalVariable.PM2P5: 0.2,
            EnvironmentalVariable.PM10: 0.2,
            EnvironmentalVariable.OZONE: 0.2,
            EnvironmentalVariable.NO2: 0.2,
            EnvironmentalVariable.SO2: 0.1,
            EnvironmentalVariable.UV: 0.1
        },
        description="Healthy adult seeking general environmental overview"
    ),
    HealthProfile.ASTHMA_CHILD: HealthProfileConfig(
        name=HealthProfile.ASTHMA_CHILD,
        weights={
            EnvironmentalVariable.PM2P5: 0.3,
            EnvironmentalVariable.PM10: 0.2,
            EnvironmentalVariable.OZONE: 0.2,
            EnvironmentalVariable.NO2: 0.2,
            EnvironmentalVariable.SO2: 0.1
        },
        description="Child with asthma requiring careful monitoring"
    ),
    HealthProfile.SEASONAL_ALLERGIC_RHINITIS: HealthProfileConfig(
        name=HealthProfile.SEASONAL_ALLERGIC_RHINITIS,
        weights={
            EnvironmentalVariable.BIRCH_POLLEN: 0.4,
            EnvironmentalVariable.GRASS_POLLEN: 0.4,
            EnvironmentalVariable.PM2P5: 0.2
        },
        description="Seasonal allergic rhinitis (hay-fever)"
    ),
    HealthProfile.ALLERGIC_ASTHMA: HealthProfileConfig(
        name=HealthProfile.ALLERGIC_ASTHMA,
        weights={
            EnvironmentalVariable.OZONE: 0.4,
            EnvironmentalVariable.PM2P5: 0.3,
            EnvironmentalVariable.BIRCH_POLLEN: 0.15,
            EnvironmentalVariable.GRASS_POLLEN: 0.15
        },
        description="Allergic (extrinsic) asthma"
    ),
    HealthProfile.COPD: HealthProfileConfig(
        name=HealthProfile.COPD,
        weights={
            EnvironmentalVariable.PM2P5: 0.5,
            EnvironmentalVariable.NO2: 0.3,
            EnvironmentalVariable.OZONE: 0.2
        },
        description="Chronic Obstructive Pulmonary Disease (COPD)"
    ),
    HealthProfile.ISCHAEMIC_HEART_DISEASE: HealthProfileConfig(
        name=HealthProfile.ISCHAEMIC_HEART_DISEASE,
        weights={
            EnvironmentalVariable.PM2P5: 0.7,
            EnvironmentalVariable.NO2: 0.3
        },
        description="Ischaemic heart disease / heart-failure"
    ),
    HealthProfile.TYPE2_DIABETES: HealthProfileConfig(
        name=HealthProfile.TYPE2_DIABETES,
        weights={
            EnvironmentalVariable.PM2P5: 0.6,
            EnvironmentalVariable.NO2: 0.4
        },
        description="Type-2 diabetes with cardio-metabolic risk"
    ),
    HealthProfile.PREGNANCY: HealthProfileConfig(
        name=HealthProfile.PREGNANCY,
        weights={
            EnvironmentalVariable.OZONE: 0.6,
            EnvironmentalVariable.PM2P5: 0.4
        },
        description="Pregnancy (pre-eclampsia / pre-term risk)"
    ),
    HealthProfile.SKIN_CANCER_SURVIVOR: HealthProfileConfig(
        name=HealthProfile.SKIN_CANCER_SURVIVOR,
        weights={
            EnvironmentalVariable.UV: 1.0
        },
        description="Skin-cancer survivors & high-UV phenotypes (Fitzpatrick I–II)"
    ),
    HealthProfile.VITILIGO: HealthProfileConfig(
        name=HealthProfile.VITILIGO,
        weights={
            EnvironmentalVariable.UV: 1.0
        },
        description="Vitiligo / albinism (pigment-loss disorders)"
    ),
    HealthProfile.LUPUS: HealthProfileConfig(
        name=HealthProfile.LUPUS,
        weights={
            EnvironmentalVariable.UV: 0.8,
            EnvironmentalVariable.PM2P5: 0.2
        },
        description="Systemic lupus erythematosus (photosensitive)"
    ),
    HealthProfile.ALLERGIC_CONJUNCTIVITIS: HealthProfileConfig(
        name=HealthProfile.ALLERGIC_CONJUNCTIVITIS,
        weights={
            EnvironmentalVariable.PM10: 0.4,
            EnvironmentalVariable.NO2: 0.3,
            EnvironmentalVariable.BIRCH_POLLEN: 0.15,
            EnvironmentalVariable.GRASS_POLLEN: 0.15
        },
        description="Allergic conjunctivitis & other ocular allergies"
    ),
    HealthProfile.ATOPIC_DERMATITIS: HealthProfileConfig(
        name=HealthProfile.ATOPIC_DERMATITIS,
        weights={
            EnvironmentalVariable.PM2P5: 0.7,
            EnvironmentalVariable.OZONE: 0.3
        },
        description="Atopic dermatitis (eczema)"
    )
}

# Constants for SAFE/DANGER thresholds
THRESHOLDS: Dict[EnvironmentalVariable, ThresholdConfig] = {
    EnvironmentalVariable.PM2P5: {'safe': 15, 'danger': 75, 'unit': 'µg m⁻³', 'window': '24h'},
    EnvironmentalVariable.PM10: {'safe': 45, 'danger': 150, 'unit': 'µg m⁻³', 'window': '24h'},
    EnvironmentalVariable.NO2: {'safe': 50, 'danger': 340, 'unit': 'µg m⁻³', 'window': '1h'},
    EnvironmentalVariable.OZONE: {'safe': 60, 'danger': 240, 'unit': 'µg m⁻³', 'window': '8h'},
    EnvironmentalVariable.SO2: {'safe': 40, 'danger': 500, 'unit': 'µg m⁻³', 'window': '1h'},
    EnvironmentalVariable.BIRCH_POLLEN: {'safe': 10, 'danger': 1000, 'unit': 'grains m⁻³', 'window': '24h'},
    EnvironmentalVariable.GRASS_POLLEN: {'safe': 10, 'danger': 250, 'unit': 'grains m⁻³', 'window': '24h'},
    EnvironmentalVariable.OLIVE_POLLEN: {'safe': 10, 'danger': 150, 'unit': 'grains m⁻³', 'window': '24h'},
    EnvironmentalVariable.MUGWORT_POLLEN: {'safe': 10, 'danger': 150, 'unit': 'grains m⁻³', 'window': '24h'},
    EnvironmentalVariable.RAGWEED_POLLEN: {'safe': 10, 'danger': 150, 'unit': 'grains m⁻³', 'window': '24h'},
    EnvironmentalVariable.ALDER_POLLEN: {'safe': 10, 'danger': 150, 'unit': 'grains m⁻³', 'window': '24h'},
    EnvironmentalVariable.UV: {'safe': 2, 'danger': 11, 'unit': 'index', 'window': 'instant'}
}

# Timing and threshold constants for hourly risk assessment
VARIABLE_TIMING: Dict[EnvironmentalVariable, VariableTimingConfig] = {
    EnvironmentalVariable.UV: {
        'window': 'instant',
        'alert_threshold': 3,
        'relevant_profiles': [
            HealthProfile.SKIN_CANCER_SURVIVOR,
            HealthProfile.VITILIGO,
            HealthProfile.LUPUS
        ]
    },
    EnvironmentalVariable.OZONE: {
        'window': '8h',
        'alert_threshold': 120,  # µg/m³
        'relevant_profiles': [
            HealthProfile.ALLERGIC_ASTHMA,
            HealthProfile.COPD,
            HealthProfile.PREGNANCY,
            HealthProfile.ATOPIC_DERMATITIS
        ]
    },
    EnvironmentalVariable.NO2: {
        'window': '1h',
        'alert_threshold': 100,  # µg/m³
        'relevant_profiles': [
            HealthProfile.ALLERGIC_ASTHMA,
            HealthProfile.COPD,
            HealthProfile.ISCHAEMIC_HEART_DISEASE,
            HealthProfile.TYPE2_DIABETES,
            HealthProfile.ALLERGIC_CONJUNCTIVITIS
        ]
    },
    EnvironmentalVariable.PM2P5: {
        'window': '24h',
        'alert_threshold': 35,  # µg/m³
        'relevant_profiles': [
            HealthProfile.ALLERGIC_ASTHMA,
            HealthProfile.COPD,
            HealthProfile.ISCHAEMIC_HEART_DISEASE,
            HealthProfile.TYPE2_DIABETES,
            HealthProfile.PREGNANCY,
            HealthProfile.ALLERGIC_CONJUNCTIVITIS,
            HealthProfile.ATOPIC_DERMATITIS
        ]
    },
    EnvironmentalVariable.PM10: {
        'window': '24h',
        'alert_threshold': 35,  # µg/m³
        'relevant_profiles': [
            HealthProfile.ALLERGIC_CONJUNCTIVITIS
        ]
    },
    EnvironmentalVariable.SO2: {
        'window': '1h',
        'alert_threshold': 125,  # µg/m³
        'relevant_profiles': [
            HealthProfile.ALLERGIC_ASTHMA,
            HealthProfile.COPD
        ]
    }
}

# Pollen cross-reactivity groups
POLLEN_GROUPS = {
    'BETULACEAE': [EnvironmentalVariable.BIRCH_POLLEN, EnvironmentalVariable.ALDER_POLLEN],
    'ASTERACEAE': [EnvironmentalVariable.MUGWORT_POLLEN, EnvironmentalVariable.RAGWEED_POLLEN],
    'GRASS': [EnvironmentalVariable.GRASS_POLLEN],
    'OLIVE': [EnvironmentalVariable.OLIVE_POLLEN]
}

@dataclass
class TimeWindow:
    """Represents a time window where risk exceeds threshold."""
    start: datetime
    end: datetime
    value: float  # The actual value during this window

@dataclass
class RiskAssessment:
    """Container for risk assessment results."""
    final_score: int
    sub_scores: Dict[EnvironmentalVariable, int]
    top_contributor: Tuple[EnvironmentalVariable, int]
    beyond_scale: bool = False
    confidence: float = 1.0
    risk_windows: Dict[EnvironmentalVariable, List[TimeWindow]] = field(default_factory=dict)
    missing_variables: List[EnvironmentalVariable] = field(default_factory=list)
    extreme_events: Dict[EnvironmentalVariable, float] = field(default_factory=dict)

class DataError(Exception):
    """Base class for data-related errors."""
    pass

class MissingDataError(DataError):
    """Raised when required data is missing."""
    pass

class InvalidDataError(DataError):
    """Raised when data is invalid (e.g., negative values)."""
    pass

def validate_data(data: xr.DataArray, var: EnvironmentalVariable) -> None:
    """
    Validate environmental data for a specific variable.
    
    Args:
        data: The data array to validate
        var: The environmental variable being validated
        
    Raises:
        InvalidDataError: If data contains invalid values
    """
    if np.any(np.isnan(data)):
        logger.warning(f"NaN values found in {var.value} data")
    
    if np.any(data < 0):
        raise InvalidDataError(f"Negative values found in {var.value} data")
    
    if var in [EnvironmentalVariable.UV, EnvironmentalVariable.PM2P5, EnvironmentalVariable.PM10]:
        if np.any(data > THRESHOLDS[var]['danger'] * 2):
            logger.warning(f"Extreme values (>2x danger threshold) found in {var.value} data")

def calculate_hazard_fraction(value: float, safe: float, danger: float) -> float:
    """
    Calculate hazard fraction (0-1) for a single driver.
    
    Args:
        value: The measured value
        safe: The safe threshold
        danger: The danger threshold
        
    Returns:
        float: Hazard fraction between 0 and 1
    """
    return max(0.0, min(1.0, (value - safe) / (danger - safe)))

def calculate_sub_score(hazard_fraction: float, curve: str = 'linear', sensitivity: float = 1.0) -> int:
    """
    Convert hazard fraction to 1-10 sub-score.
    
    Args:
        hazard_fraction: The calculated hazard fraction
        curve: The curve type ('linear' or 'logistic')
        sensitivity: The sensitivity adjustment factor
        
    Returns:
        int: Score between 1 and 10
    """
    if curve == 'logistic':
        hazard_fraction = 1/(1 + math.exp(-12*(hazard_fraction-0.5)))
    hazard_fraction = hazard_fraction**sensitivity
    return int(round(1 + 9*hazard_fraction))

def calculate_pollen_score(pollen_values: Dict[EnvironmentalVariable, float]) -> int:
    """
    Calculate combined pollen score considering cross-reactivity.
    
    Args:
        pollen_values: Dictionary of pollen type to value
        
    Returns:
        int: Combined pollen score between 1 and 10
    """
    hazard_fractions = {
        name: calculate_hazard_fraction(value, THRESHOLDS[name]['safe'], THRESHOLDS[name]['danger'])
        for name, value in pollen_values.items()
    }
    
    group_hazards = {}
    for group, members in POLLEN_GROUPS.items():
        group_hazards[group] = max(hazard_fractions.get(member, 0) for member in members)
    
    total_fraction = 1 - math.prod(1 - H for H in group_hazards.values())
    return int(round(1 + 9*total_fraction))

def detect_peak_periods(
    data: xr.DataArray,
    var: EnvironmentalVariable,
    threshold: float,
    min_duration: int = 3
) -> List[TimeWindow]:
    """
    Detect periods where values exceed threshold and form significant peaks.
    
    Args:
        data: The data array to analyze
        var: The environmental variable being analyzed
        threshold: The threshold value
        min_duration: Minimum duration in hours for a peak period
        
    Returns:
        List[TimeWindow]: List of detected peak periods
    """
    try:
        validate_data(data, var)
    except DataError as e:
        logger.error(f"Data validation failed for {var.value}: {str(e)}")
        return []
    
    windows = []
    
    if var in VARIABLE_TIMING:
        timing = VARIABLE_TIMING[var]
        
        if timing['window'] == 'instant':
            # For instant measurements
            high_hours = data > threshold
            in_window = False
            window_start = None
            window_max = 0
            
            for time, value in zip(data.time.values, data.values):
                if high_hours.sel(time=time) and not in_window:
                    in_window = True
                    window_start = time
                    window_max = value
                elif high_hours.sel(time=time) and in_window:
                    window_max = max(window_max, value)
                elif not high_hours.sel(time=time) and in_window:
                    if (time - window_start).astype('timedelta64[h]').astype(int) >= min_duration:
                        windows.append(TimeWindow(
                            start=window_start,
                            end=time,
                            value=window_max
                        ))
                    in_window = False
            
            if in_window:
                if (data.time.values[-1] - window_start).astype('timedelta64[h]').astype(int) >= min_duration:
                    windows.append(TimeWindow(
                        start=window_start,
                        end=data.time.values[-1],
                        value=window_max
                    ))
            
        elif timing['window'] == '8h':
            # For 8-hour rolling windows (O3)
            rolling = data.rolling(time=8).mean()
            high_hours = rolling > threshold
            in_window = False
            window_start = None
            window_max = 0
            
            for time, value in zip(rolling.time.values, rolling.values):
                if high_hours.sel(time=time) and not in_window:
                    in_window = True
                    window_start = time
                    window_max = value
                elif high_hours.sel(time=time) and in_window:
                    window_max = max(window_max, value)
                elif not high_hours.sel(time=time) and in_window:
                    if (time - window_start).astype('timedelta64[h]').astype(int) >= min_duration:
                        windows.append(TimeWindow(
                            start=window_start,
                            end=time,
                            value=window_max
                        ))
                    in_window = False
            
            if in_window:
                if (rolling.time.values[-1] - window_start).astype('timedelta64[h]').astype(int) >= min_duration:
                    windows.append(TimeWindow(
                        start=window_start,
                        end=rolling.time.values[-1],
                        value=window_max
                    ))
            
        elif timing['window'] == '24h':
            # For 24-hour rolling windows (PM2.5, PM10)
            rolling = data.rolling(time=24).mean()
            high_hours = rolling > threshold
            in_window = False
            window_start = None
            window_max = 0
            
            for time, value in zip(rolling.time.values, rolling.values):
                if high_hours.sel(time=time) and not in_window:
                    in_window = True
                    window_start = time
                    window_max = value
                elif high_hours.sel(time=time) and in_window:
                    window_max = max(window_max, value)
                elif not high_hours.sel(time=time) and in_window:
                    if (time - window_start).astype('timedelta64[h]').astype(int) >= min_duration:
                        windows.append(TimeWindow(
                            start=window_start,
                            end=time,
                            value=window_max
                        ))
                    in_window = False
            
            if in_window:
                if (rolling.time.values[-1] - window_start).astype('timedelta64[h]').astype(int) >= min_duration:
                    windows.append(TimeWindow(
                        start=window_start,
                        end=rolling.time.values[-1],
                        value=window_max
                    ))
    
    return windows

def calculate_risk_windows(
    data: xr.DataArray,
    var: EnvironmentalVariable
) -> List[TimeWindow]:
    """
    Calculate risk windows based on variable-specific thresholds and timing patterns.
    
    Args:
        data: The data array to analyze
        var: The environmental variable being analyzed
        
    Returns:
        List[TimeWindow]: List of detected risk windows
    """
    if var in VARIABLE_TIMING:
        return detect_peak_periods(data, var, VARIABLE_TIMING[var]['alert_threshold'])
    return []

def calculate_profile_risk(
    profile: HealthProfile,
    environmental_data: Dict[EnvironmentalVariable, xr.DataArray],
    sensitivity: Optional[float] = None
) -> RiskAssessment:
    """
    Calculate risk score for a health profile.
    
    Args:
        profile: The health profile to assess
        environmental_data: Dictionary of environmental variables to their data
        sensitivity: Optional sensitivity override (default: None)
        
    Returns:
        RiskAssessment: The calculated risk assessment
        
    Raises:
        MissingDataError: If required data is missing
    """
    sub_scores = {}
    missing_variables = []
    extreme_events = {}
    beyond_scale = False
    
    # Calculate sub-scores for each driver
    for var, weight in HEALTH_PROFILES[profile].weights.items():
        if var in environmental_data:
            try:
                data = environmental_data[var]
                validate_data(data, var)
                value = float(data.mean())
                
                # Check for extreme events
                if value > THRESHOLDS[var]['danger'] * 1.5:
                    beyond_scale = True
                    extreme_events[var] = value
                    value = THRESHOLDS[var]['danger']  # Cap at danger threshold
                
                # Special handling for pollen
                if var in [p for group in POLLEN_GROUPS.values() for p in group]:
                    pollen_values = {var: value}
                    sub_scores[var] = calculate_pollen_score(pollen_values)
                else:
                    hazard = calculate_hazard_fraction(value, THRESHOLDS[var]['safe'], THRESHOLDS[var]['danger'])
                    # For asthma child, use more conservative thresholds
                    if profile == HealthProfile.ASTHMA_CHILD:
                        hazard = hazard * 1.2  # Increase hazard by 20% for children
                    sub_scores[var] = calculate_sub_score(hazard)
                
            except DataError as e:
                logger.error(f"Error processing {var.value}: {str(e)}")
                missing_variables.append(var)
                sub_scores[var] = 1  # Default to lowest risk
        else:
            missing_variables.append(var)
            sub_scores[var] = 1  # Default to lowest risk
    
    # Calculate confidence based on missing data
    confidence = 1.0
    if missing_variables:
        required_vars = set(HEALTH_PROFILES[profile].weights.keys())
        missing_ratio = len(missing_variables) / len(required_vars)
        confidence = 1.0 - (missing_ratio * 0.5)  # Reduce confidence by up to 50%
    
    # Calculate final score
    final_score = round(sum(w * sub_scores[d] for d, w in HEALTH_PROFILES[profile].weights.items()))
    
    # Dominant-pollutant override
    if any(score >= 9 for score in sub_scores.values()):
        final_score = max(sub_scores.values())
    
    # Find top contributor
    top_contributor = max(sub_scores.items(), key=lambda x: x[1])
    
    # Calculate risk windows
    risk_windows = {}
    for var in environmental_data:
        if var in VARIABLE_TIMING:
            risk_windows[var] = calculate_risk_windows(environmental_data[var], var)
    
    return RiskAssessment(
        final_score=final_score,
        sub_scores=sub_scores,
        top_contributor=top_contributor,
        beyond_scale=beyond_scale,
        confidence=confidence,
        risk_windows=risk_windows,
        missing_variables=missing_variables,
        extreme_events=extreme_events
    )

def load_environmental_data(date: str) -> Dict[EnvironmentalVariable, xr.DataArray]:
    """
    Load all environmental data for a given date.
    
    Args:
        date: The date to load data for
        
    Returns:
        Dict[EnvironmentalVariable, xr.DataArray]: Dictionary of loaded data
        
    Raises:
        MissingDataError: If no data could be loaded
    """
    data_dir = Path('data')
    data = {}
    
    for var in EnvironmentalVariable:
        if var == EnvironmentalVariable.UV:
            file_path = data_dir / f"{date}_{var.value}.tif"
        else:
            file_path = data_dir / f"{date}_{var.value}.tif"
        
        if file_path.exists():
            try:
                data[var] = xr.open_dataarray(file_path)
            except Exception as e:
                logger.error(f"Error loading {var.value} data: {str(e)}")
    
    if not data:
        raise MissingDataError(f"No environmental data found for date {date}")
    
    return data

def main():
    """Main function to demonstrate risk calculation."""
    try:
        date = "2025-06-05"  # Use today's date
        environmental_data = load_environmental_data(date)
        
        # Calculate risk for each profile
        for profile in HealthProfile:
            try:
                risk_assessment = calculate_profile_risk(profile, environmental_data)
                print(f"\nRisk assessment for {profile.value}:")
                print(f"Overall risk score: {risk_assessment.final_score}")
                print(f"Confidence: {risk_assessment.confidence:.1%}")
                
                if risk_assessment.beyond_scale:
                    print("⚠️ Beyond scale values detected!")
                    for var, value in risk_assessment.extreme_events.items():
                        print(f"  {var.value}: {value:.1f} {THRESHOLDS[var]['unit']}")
                
                if risk_assessment.missing_variables:
                    print("⚠️ Missing data for:")
                    for var in risk_assessment.missing_variables:
                        print(f"  {var.value}")
                
                print("Individual variable scores:")
                for var, score in risk_assessment.sub_scores.items():
                    print(f"  {var.value}: {score}")
                print(f"Top contributor: {risk_assessment.top_contributor[0].value} ({risk_assessment.top_contributor[1]})")
                
                print("\nRisk windows:")
                for var, windows in risk_assessment.risk_windows.items():
                    if windows:
                        print(f"  {var.value}:")
                        for window in windows:
                            print(f"    {window.start} to {window.end} (value: {window.value:.1f})")
            
            except Exception as e:
                logger.error(f"Error calculating risk for {profile.value}: {str(e)}")
                continue
    
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        raise

if __name__ == "__main__":
    main() 