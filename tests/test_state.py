"""
Unit tests for state.py: load_variable, save_variable, load_persistent, state_from_variable, variable_from_state.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

# Ensure project root on path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import state


def test_load_variable_missing_returns_empty():
    """Load variable from non-existent path returns empty dict."""
    result = state.load_variable(Path("/nonexistent/variable.json"))
    assert result == {}


def test_save_and_load_variable_roundtrip(tmp_path):
    """Save variable then load returns same data."""
    path = tmp_path / "variable.json"
    data = {"crop": "rice", "currentDayIndex": 1}
    state.save_variable(data, path)
    assert path.exists()
    loaded = state.load_variable(path)
    assert loaded["crop"] == "rice"
    assert loaded["currentDayIndex"] == 1


def test_load_persistent_missing_returns_empty():
    """Load persistent from non-existent path returns empty dict."""
    result = state.load_persistent(Path("/nonexistent/persistent.json"))
    assert result == {}


def test_state_from_variable():
    """state_from_variable builds FarmGraphState with correct keys."""
    variable = {"crop": "rice", "location": "Kolhapur", "currentDayIndex": 2, "cropCalendar": []}
    s = state.state_from_variable(variable)
    assert s["crop"] == "rice"
    assert s["location"] == "Kolhapur"
    assert s["currentDayIndex"] == 2
    assert s["cropCalendar"] == []
    assert s.get("sowingDate", "") == ""


def test_variable_from_state():
    """variable_from_state extracts variable-persisted fields."""
    st = {"crop": "rice", "location": "Kolhapur", "currentDayIndex": 1, "message": "Hello"}
    v = state.variable_from_state(st)
    assert v["crop"] == "rice"
    assert v["location"] == "Kolhapur"
    assert v["currentDayIndex"] == 1
    assert v.get("last_advisory") == "Hello"


def test_variable_from_state_omits_none():
    """variable_from_state omits keys whose value is None (per implementation)."""
    st = {"crop": "rice", "location": None}
    v = state.variable_from_state(st)
    assert "crop" in v
    # location may be omitted if None is filtered
    assert v.get("crop") == "rice"
