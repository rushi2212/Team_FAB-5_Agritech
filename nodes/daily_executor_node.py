"""
Node 4: DailyExecutorNode – pick today's actions from cropCalendar; read-only on calendar.
"""
from __future__ import annotations

from typing import Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import state as state_module
from state import FarmGraphState, load_variable


def daily_executor_node(state: FarmGraphState) -> dict[str, Any]:
    """Return todayActions for currentDayIndex from variable.json cropCalendar."""
    variable = load_variable(state_module.VARIABLE_JSON)
    current_day = variable.get("currentDayIndex", state.get("currentDayIndex", 0))
    calendar = variable.get("cropCalendar") or state.get("cropCalendar") or []

    today_actions: list[str] = []
    current_stage = ""
    for entry in calendar:
        if entry.get("day") == current_day:
            today_actions.extend(entry.get("actions") or [])
            current_stage = entry.get("stage", "")
        elif entry.get("day", 0) <= current_day and not current_stage:
            current_stage = entry.get("stage", "")

    # If no entry for exact day, use latest stage that has started
    if not today_actions and calendar:
        for entry in reversed(calendar):
            if entry.get("day", 0) <= current_day:
                current_stage = entry.get("stage", "")
                break

    return {
        "todayActions": today_actions,
        "currentCropStage": current_stage or state.get("currentCropStage", ""),
    }
