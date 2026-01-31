"""
Node 6: RiskDetectionNode – detect action failures/conflicts (e.g. spray blocked by rain).
"""
from __future__ import annotations

from typing import Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import state as state_module
from state import FarmGraphState, load_variable, save_variable, RiskEvent
from knowledge.loaders import get_replanning_rules


def risk_detection_node(state: FarmGraphState) -> dict[str, Any]:
    """Set riskEvent if today's action is blocked by weather (e.g. rain). Write to variable."""
    today_actions = state.get("todayActions") or []
    weather_risk = state.get("weatherRisk") or "CLEAR"
    variable = load_variable(state_module.VARIABLE_JSON)

    rules = get_replanning_rules()
    rain_blocked = rules.get("rainBlockedActions") or []
    if not rain_blocked:
        rain_blocked = ["Fungicide spray", "First nitrogen application", "Second nitrogen if needed"]

    risk_event: RiskEvent | None = None
    for action in today_actions:
        if weather_risk == "RAIN_EXPECTED" and any(b in action for b in rain_blocked):
            risk_event = {"type": "ACTION_BLOCKED", "reason": "Rain"}
            break
        if weather_risk == "HEATWAVE":
            risk_event = {"type": "HEAT_STRESS", "reason": "Heatwave"}
            break

    risk_events_list = variable.get("riskEvents") or []
    if risk_event:
        risk_events_list.append(risk_event)
    variable["riskEvent"] = risk_event
    variable["riskEvents"] = risk_events_list
    save_variable(variable, state_module.VARIABLE_JSON)

    return {"riskEvent": risk_event, "riskEvents": risk_events_list}
