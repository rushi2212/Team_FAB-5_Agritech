"""
Node 7: CalendarReplannerNode – update remaining calendar when risk (e.g. rain); write to variable.json.
"""
from __future__ import annotations

from typing import Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import state as state_module
from state import FarmGraphState, load_variable, save_variable, CalendarEntry
from knowledge.loaders import get_replanning_rules


def calendar_replanner_node(state: FarmGraphState) -> dict[str, Any]:
    """Reschedule blocked actions using persistent rules; merge updated remaining calendar into variable.json."""
    variable = load_variable(state_module.VARIABLE_JSON)
    risk_event = state.get("riskEvent") or variable.get("riskEvent")
    if not risk_event:
        return {}

    current_day = variable.get("currentDayIndex", state.get("currentDayIndex", 0))
    calendar = variable.get("cropCalendar") or state.get("cropCalendar") or []
    crop = variable.get("crop") or state.get("crop") or ""
    rules = get_replanning_rules()
    max_delay = rules.get("sprayDelayToleranceDays", 3)

    # Remaining calendar: from current_day onward
    past = [e for e in calendar if e.get("day", 0) < current_day]
    remaining = [e for e in calendar if e.get("day", 0) >= current_day]

    failed_reason = risk_event.get("reason", "")
    today_actions = state.get("todayActions") or []

    updated_remaining: list[CalendarEntry] = []
    # Reschedule: move today's blocked actions to next dry window (e.g. +2 days)
    reschedule_day = current_day + 2
    if reschedule_day > current_day + max_delay:
        reschedule_day = current_day + max_delay

    for entry in remaining:
        day = entry.get("day", 0)
        actions = list(entry.get("actions") or [])
        stage = entry.get("stage", "")

        if day == current_day and failed_reason == "Rain":
            rescheduled_actions = [a + " (rescheduled)" for a in actions if a in today_actions]
            if rescheduled_actions:
                updated_remaining.append({
                    "day": reschedule_day,
                    "stage": stage,
                    "actions": rescheduled_actions,
                    "dependencies": entry.get("dependencies", []),
                    "weatherConstraints": entry.get("weatherConstraints", []),
                })
            other_actions = [a for a in actions if a not in today_actions]
            updated_remaining.append({
                "day": current_day,
                "stage": "Monitoring" if not other_actions else stage,
                "actions": other_actions if other_actions else ["Field scouting"],
                "dependencies": [],
                "weatherConstraints": [],
            })
        else:
            updated_remaining.append(entry)

    updated_remaining.sort(key=lambda e: e.get("day", 0))
    full_calendar = past + updated_remaining
    variable["cropCalendar"] = full_calendar
    save_variable(variable, state_module.VARIABLE_JSON)

    return {"cropCalendar": full_calendar}
