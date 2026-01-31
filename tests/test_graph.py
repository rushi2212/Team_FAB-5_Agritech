"""
Integration tests: run full graph with test data and assert final state and variable.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from graph import run_once


def test_run_once_creates_calendar_and_advisory(patch_data_paths):
    """run_once with patched temp paths builds calendar and sets last_advisory."""
    variable_path = patch_data_paths["variable_json"]
    # Ensure minimal variable so planner can build calendar
    variable_path.write_text(json.dumps({
        "crop": "rice",
        "location": "Kolhapur",
        "sowingDate": "2026-06-15",
        "currentDayIndex": 0,
        "cropCalendar": [],
        "weatherForecast": {},
        "weatherHistory": [],
        "completedActions": [],
        "skippedActions": [],
        "delayedActions": [],
        "riskEvents": [],
        "confidenceScores": {},
    }, indent=2), encoding="utf-8")

    state_result = run_once(
        crop="rice",
        location="Kolhapur",
        sowing_date="2026-06-15",
        variable_path=variable_path,
    )

    assert state_result.get("message")
    data = json.loads(variable_path.read_text(encoding="utf-8"))
    assert len(data.get("cropCalendar", [])) >= 1
    assert "currentDayIndex" in data
    assert data.get("last_advisory")
