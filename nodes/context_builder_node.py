"""
Node 2: ContextBuilderNode – build soilContext, weatherForecast, weatherHistory from persistent + variable.
"""
from __future__ import annotations

from typing import Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import state as state_module
from state import FarmGraphState, load_variable, save_variable, variable_from_state
from knowledge.loaders import get_soil_rules


def context_builder_node(state: FarmGraphState) -> dict[str, Any]:
    """Build baseline context from persistent (soil rules, regional) and variable (weather history)."""
    location = state.get("location") or ""
    variable = load_variable(state_module.VARIABLE_JSON)

    soil_rules = get_soil_rules(location)
    regional = soil_rules.get("regional") or {}
    defaults = soil_rules.get("defaults", {})
    soil_type = regional.get("soilType") or "clay"
    soil_default = defaults.get(soil_type, {})
    ph = regional.get("ph") or soil_default.get("ph_range", [6.0, 7.0])
    if isinstance(ph, list):
        ph = (ph[0] + ph[1]) / 2 if ph else 6.5

    soil_context = {
        "type": soil_type,
        "ph": ph,
        "advice": soil_default.get("nitrogen_advice", "standard"),
    }

    weather_forecast = variable.get("weatherForecast") or state.get("weatherForecast") or {}
    weather_history = variable.get("weatherHistory") or state.get("weatherHistory") or []

    # Optional: if we had a weather API we'd fetch and set weatherForecast here
    if not weather_forecast and state.get("location"):
        weather_forecast = {"15_day": [], "expectedPattern": "monsoon"}

    updates = {
        "soilContext": soil_context,
        "weatherForecast": weather_forecast,
        "weatherHistory": weather_history,
        "expectedWeatherPattern": weather_forecast.get("expectedPattern", "monsoon"),
    }

    # Optionally write fetched weather into variable for today
    new_state = {**state, **updates}
    var_data = variable_from_state(new_state)
    var_data["weatherForecast"] = weather_forecast
    var_data["weatherHistory"] = weather_history
    var_data["soilContext"] = soil_context
    save_variable(var_data, state_module.VARIABLE_JSON)

    return updates
