"""
Load persistent.json and expose structured knowledge for CropCalendarPlannerNode and CalendarReplannerNode.
LLM reasons over this; no raw JSON passed as context.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DEFAULT_PERSISTENT = Path(__file__).resolve().parent.parent / "data" / "persistent.json"


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_persistent_knowledge(path: Path | None = None) -> dict[str, Any]:
    """Load full persistent store."""
    return _load(path or _DEFAULT_PERSISTENT)


def get_crop_lifecycle(crop: str, path: Path | None = None) -> list[dict[str, Any]]:
    """Return stage-wise crop lifecycle for the given crop (from stageModels)."""
    data = load_persistent_knowledge(path)
    models = data.get("stageModels", {})
    return models.get(crop, [])


def get_stage_rules(crop: str, path: Path | None = None) -> dict[str, Any]:
    """Return stage rules including dependencies and weather constraints for the crop."""
    lifecycle = get_crop_lifecycle(crop, path)
    return {
        "stages": lifecycle,
        "stageNames": [s.get("stage", "") for s in lifecycle],
        "dependencies": {s.get("stage", ""): s.get("dependencies", []) for s in lifecycle},
        "weatherConstraints": {s.get("stage", ""): s.get("weatherConstraints", []) for s in lifecycle},
    }


def get_soil_rules(location: str | None = None, path: Path | None = None) -> dict[str, Any]:
    """Return soil rules and regional defaults."""
    data = load_persistent_knowledge(path)
    soil = data.get("soilRules", {})
    defaults = soil.get("defaults", {})
    regional = soil.get("regionalDefaults", {})
    out = {"defaults": defaults}
    if location and location in regional:
        out["regional"] = regional[location]
    return out


def get_crop_catalog(path: Path | None = None) -> list[dict[str, Any]]:
    """Return crop catalog for intent validation."""
    data = load_persistent_knowledge(path)
    return data.get("cropCatalog", [])


def get_replanning_rules(path: Path | None = None) -> dict[str, Any]:
    """Return replanning rules: spray delay tolerance, rain-blocked actions, alternatives, weather windows."""
    data = load_persistent_knowledge(path)
    return data.get("replanningRules", {})
