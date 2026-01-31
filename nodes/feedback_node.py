"""
Node 9: FeedbackNode – learn from execution; update currentDayIndex, completed/skipped/delayed; write variable.json.
"""
from __future__ import annotations

from typing import Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import state as state_module
from state import FarmGraphState, load_variable, save_variable


def feedback_node(state: FarmGraphState) -> dict[str, Any]:
    """Increment currentDayIndex; append completed/skipped/delayed; update confidence; persist to variable.json."""
    variable = load_variable(state_module.VARIABLE_JSON)
    farmer_response = state.get("farmer_response") or variable.get("farmer_response") or ""
    current_day = variable.get("currentDayIndex", state.get("currentDayIndex", 0))
    today_actions = state.get("todayActions") or []
    risk_event = state.get("riskEvent") or variable.get("riskEvent")

    completed = list(variable.get("completedActions") or [])
    skipped = list(variable.get("skippedActions") or [])
    delayed = list(variable.get("delayedActions") or [])
    confidence = dict(variable.get("confidenceScores") or {})

    if farmer_response == "did_not_spray" or (risk_event and risk_event.get("type") == "ACTION_BLOCKED"):
        for a in today_actions:
            skipped.append({"action": a, "day": current_day, "reason": "blocked"})
        confidence["spray_skip"] = confidence.get("spray_skip", 0) + 0.1
    elif farmer_response == "completed":
        for a in today_actions:
            completed.append({"action": a, "day": current_day})
        confidence["completion"] = confidence.get("completion", 0) + 0.1
    else:
        for a in today_actions:
            delayed.append({"action": a, "day": current_day})

    next_day = current_day + 1
    variable["currentDayIndex"] = next_day
    variable["completedActions"] = completed
    variable["skippedActions"] = skipped
    variable["delayedActions"] = delayed
    variable["confidenceScores"] = confidence
    variable["riskEvent"] = None
    save_variable(variable, state_module.VARIABLE_JSON)

    return {
        "currentDayIndex": next_day,
        "completedActions": completed,
        "skippedActions": skipped,
        "delayedActions": delayed,
        "confidenceScores": confidence,
    }
