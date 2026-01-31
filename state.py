"""
FarmGraphState and persistence helpers for variable.json and persistent.json.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict

# Default paths; override via env or arguments
DATA_DIR = Path(__file__).resolve().parent / "data"
VARIABLE_JSON = DATA_DIR / "variable.json"
PERSISTENT_JSON = DATA_DIR / "persistent.json"


class CalendarEntry(TypedDict, total=False):
    day: int
    stage: str
    actions: list[str]
    dependencies: list[str]
    weatherConstraints: list[str]


class RiskEvent(TypedDict, total=False):
    type: str  # e.g. ACTION_BLOCKED
    reason: str  # e.g. Rain


class FarmGraphState(TypedDict, total=False):
    farmerProfile: dict[str, Any]
    location: str
    crop: str
    sowingDate: str

    soilContext: dict[str, Any]
    weatherForecast: dict[str, Any]
    weatherHistory: list[dict[str, Any]]

    cropCalendar: list[CalendarEntry]
    currentDayIndex: int
    currentCropStage: str

    completedActions: list[dict[str, Any]]
    skippedActions: list[dict[str, Any]]
    delayedActions: list[dict[str, Any]]

    riskEvents: list[RiskEvent]
    confidenceScores: dict[str, float]

    knowledgeSourcesUsed: list[str]

    # Daily execution
    todayActions: list[str]
    weatherRisk: str
    riskEvent: RiskEvent | None
    message: str
    farmer_response: str

    # For replanning
    expectedWeatherPattern: str


def load_variable(path: Path | None = None) -> dict[str, Any]:
    """Load variable state from variable.json. Returns empty dict if missing."""
    p = path or VARIABLE_JSON
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_variable(state: dict[str, Any], path: Path | None = None) -> None:
    """Write variable state to variable.json."""
    p = path or VARIABLE_JSON
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def load_persistent(path: Path | None = None) -> dict[str, Any]:
    """Load persistent rules/knowledge from persistent.json. Returns empty dict if missing."""
    p = path or PERSISTENT_JSON
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def state_from_variable(variable: dict[str, Any]) -> FarmGraphState:
    """Build FarmGraphState from variable.json contents."""
    return FarmGraphState(
        farmerProfile=variable.get("farmerProfile"),
        location=variable.get("location", ""),
        crop=variable.get("crop", ""),
        sowingDate=variable.get("sowingDate", ""),
        soilContext=variable.get("soilContext"),
        weatherForecast=variable.get("weatherForecast"),
        weatherHistory=variable.get("weatherHistory", []),
        cropCalendar=variable.get("cropCalendar", []),
        currentDayIndex=variable.get("currentDayIndex", 0),
        currentCropStage=variable.get("currentCropStage", ""),
        completedActions=variable.get("completedActions", []),
        skippedActions=variable.get("skippedActions", []),
        delayedActions=variable.get("delayedActions", []),
        riskEvents=variable.get("riskEvents", []),
        confidenceScores=variable.get("confidenceScores", {}),
        knowledgeSourcesUsed=variable.get("knowledgeSourcesUsed", []),
    )


def variable_from_state(state: FarmGraphState) -> dict[str, Any]:
    """Extract variable-persisted fields from FarmGraphState for writing to variable.json."""
    return {
        k: v
        for k, v in {
            "farmerProfile": state.get("farmerProfile"),
            "location": state.get("location"),
            "crop": state.get("crop"),
            "sowingDate": state.get("sowingDate"),
            "soilContext": state.get("soilContext"),
            "weatherForecast": state.get("weatherForecast"),
            "weatherHistory": state.get("weatherHistory", []),
            "cropCalendar": state.get("cropCalendar", []),
            "currentDayIndex": state.get("currentDayIndex", 0),
            "currentCropStage": state.get("currentCropStage", ""),
            "completedActions": state.get("completedActions", []),
            "skippedActions": state.get("skippedActions", []),
            "delayedActions": state.get("delayedActions", []),
            "riskEvents": state.get("riskEvents", []),
            "confidenceScores": state.get("confidenceScores", {}),
            "knowledgeSourcesUsed": state.get("knowledgeSourcesUsed", []),
            "last_advisory": state.get("message"),
        }.items()
        if v is not None
    }
