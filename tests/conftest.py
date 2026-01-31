"""
Pytest fixtures: temp data dir, variable.json and persistent.json, path patching.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

# Project root
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PERSISTENT_SRC = DATA_DIR / "persistent.json"


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temp data dir with persistent.json (copy) and minimal variable.json."""
    dest_persistent = tmp_path / "persistent.json"
    if PERSISTENT_SRC.exists():
        shutil.copy(PERSISTENT_SRC, dest_persistent)
    else:
        dest_persistent.write_text(json.dumps({"cropCatalog": [], "stageModels": {}, "soilRules": {}, "replanningRules": {}}), encoding="utf-8")

    variable = {
        "location": "",
        "crop": "",
        "sowingDate": "",
        "currentDayIndex": 0,
        "currentCropStage": "",
        "cropCalendar": [],
        "weatherForecast": {},
        "weatherHistory": [],
        "completedActions": [],
        "skippedActions": [],
        "delayedActions": [],
        "riskEvents": [],
        "confidenceScores": {},
    }
    (tmp_path / "variable.json").write_text(json.dumps(variable, indent=2), encoding="utf-8")
    return tmp_path


@pytest.fixture
def patch_data_paths(temp_data_dir, monkeypatch):
    """Patch state and knowledge loaders to use temp data dir."""
    import state
    import knowledge.loaders as loaders

    variable_json = temp_data_dir / "variable.json"
    persistent_json = temp_data_dir / "persistent.json"

    monkeypatch.setattr(state, "VARIABLE_JSON", variable_json)
    monkeypatch.setattr(state, "PERSISTENT_JSON", persistent_json)
    monkeypatch.setattr(loaders, "_DEFAULT_PERSISTENT", persistent_json)

    return {"variable_json": variable_json, "persistent_json": persistent_json}


@pytest.fixture
def sample_state():
    """Minimal FarmGraphState for node tests."""
    return {
        "crop": "rice",
        "location": "Kolhapur",
        "sowingDate": "2026-06-15",
        "currentDayIndex": 0,
        "cropCalendar": [],
        "weatherForecast": {},
        "weatherHistory": [],
        "todayActions": [],
        "weatherRisk": "CLEAR",
        "riskEvent": None,
        "knowledgeSourcesUsed": [],
    }


@pytest.fixture
def sample_variable():
    """Minimal variable.json-like dict."""
    return {
        "crop": "rice",
        "location": "Kolhapur",
        "sowingDate": "2026-06-15",
        "currentDayIndex": 1,
        "currentCropStage": "Sowing",
        "cropCalendar": [
            {"day": 1, "stage": "Sowing", "actions": ["Seed soaking", "Field puddling"], "dependencies": [], "weatherConstraints": []},
        ],
        "weatherForecast": {},
        "weatherHistory": [],
        "completedActions": [],
        "skippedActions": [],
        "delayedActions": [],
        "riskEvents": [],
        "confidenceScores": {},
    }
