"""
Node 5: WeatherObserverNode – observe actual vs expected weather; output weatherRisk.
"""
from __future__ import annotations

from typing import Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import state as state_module
from state import FarmGraphState, load_variable, save_variable


def weather_observer_node(state: FarmGraphState) -> dict[str, Any]:
    """Set weatherRisk from forecast (e.g. rain_probability). Optionally write to variable."""
    variable = load_variable(state_module.VARIABLE_JSON)
    forecast = variable.get("weatherForecast") or state.get("weatherForecast") or {}

    rain_prob = forecast.get("rain_probability") or forecast.get("rainProbability") or 0
    if rain_prob >= 70:
        weather_risk = "RAIN_EXPECTED"
    elif forecast.get("heatwave"):
        weather_risk = "HEATWAVE"
    else:
        weather_risk = "CLEAR"

    variable["weatherRisk"] = weather_risk
    save_variable(variable, state_module.VARIABLE_JSON)

    return {"weatherRisk": weather_risk}
