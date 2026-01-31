"""
Node 3: CropCalendarPlannerNode – build full crop calendar till harvest; write to variable.json.
"""
from __future__ import annotations

from typing import Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import state as state_module
from state import FarmGraphState, save_variable, load_variable, CalendarEntry
from knowledge.loaders import get_crop_lifecycle


def crop_calendar_planner_node(state: FarmGraphState) -> dict[str, Any]:
    """Generate full cropCalendar from persistent stage model; write to variable.json."""
    crop = state.get("crop") or ""
    sowing_date = state.get("sowingDate") or ""
    soil_context = state.get("soilContext") or {}
    expected_pattern = state.get("expectedWeatherPattern") or "monsoon"

    lifecycle = get_crop_lifecycle(crop)
    if not lifecycle:
        return {"cropCalendar": [], "currentDayIndex": 0, "currentCropStage": ""}

    calendar: list[CalendarEntry] = []
    for stage_block in lifecycle:
        stage = stage_block.get("stage", "")
        day_start = stage_block.get("dayStart", 0)
        day_end = stage_block.get("dayEnd", 0)
        actions = stage_block.get("actions", [])
        deps = stage_block.get("dependencies", [])
        weather_constraints = stage_block.get("weatherConstraints", [])

        # Emit one entry per stage (or per key day); plan uses day as key
        calendar.append({
            "day": day_start,
            "stage": stage,
            "actions": actions,
            "dependencies": deps,
            "weatherConstraints": weather_constraints,
        })

    calendar.sort(key=lambda e: e.get("day", 0))
    current_day = 0
    current_stage = lifecycle[0].get("stage", "") if lifecycle else ""

    variable = load_variable(state_module.VARIABLE_JSON)
    variable["cropCalendar"] = calendar
    variable["currentDayIndex"] = current_day
    variable["currentCropStage"] = current_stage
    variable["crop"] = crop
    variable["sowingDate"] = sowing_date
    variable["location"] = state.get("location")
    variable["soilContext"] = soil_context
    save_variable(variable, state_module.VARIABLE_JSON)

    return {
        "cropCalendar": calendar,
        "currentDayIndex": current_day,
        "currentCropStage": current_stage,
        "knowledgeSourcesUsed": (state.get("knowledgeSourcesUsed") or []) + ["stage_models", "agronomy_rules"],
    }
