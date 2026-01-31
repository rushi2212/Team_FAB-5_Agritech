"""
Node 8: AdvisoryDeliveryNode – deliver short advisory to farmer (e.g. Marathi).
"""
from __future__ import annotations

from typing import Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import state as state_module
from state import FarmGraphState, load_variable, save_variable


def advisory_delivery_node(state: FarmGraphState) -> dict[str, Any]:
    """Build message from todayActions and riskEvent; optionally write last_advisory to variable."""
    today_actions = state.get("todayActions") or []
    risk_event = state.get("riskEvent")

    if risk_event and risk_event.get("type") == "ACTION_BLOCKED":
        reason = risk_event.get("reason", "weather")
        if "Rain" in reason or reason == "Rain":
            message = (
                "आज फवारणी करू नका. पाऊस अपेक्षित आहे. उद्या परिस्थिती पाहून निर्णय घेऊ."
            )
        else:
            message = f"आज planned कृती करू नका. कारण: {reason}. उद्या पुन्हा तपासा."
    elif today_actions:
        actions_str = ", ".join(today_actions)
        message = f"आज करावयाच्या कृती: {actions_str}."
    else:
        message = "आज विशिष्ट कृती नाही. शेताचे निरीक्षण करा."

    variable = load_variable(state_module.VARIABLE_JSON)
    variable["last_advisory"] = message
    save_variable(variable, state_module.VARIABLE_JSON)

    return {"message": message}
