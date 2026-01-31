"""
Unit tests for knowledge loaders: get_crop_lifecycle, get_stage_rules, get_soil_rules, get_crop_catalog, get_replanning_rules.
Uses project data/persistent.json by default; use patch_data_paths fixture to point to temp copy.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from knowledge.loaders import (
    get_crop_lifecycle,
    get_stage_rules,
    get_soil_rules,
    get_crop_catalog,
    get_replanning_rules,
    load_persistent_knowledge,
)


def test_get_crop_lifecycle_rice():
    """Rice has stage model in default persistent.json."""
    lifecycle = get_crop_lifecycle("rice")
    assert len(lifecycle) >= 1
    assert any(s.get("stage") == "Sowing" for s in lifecycle)
    assert any(s.get("stage") == "Harvest" for s in lifecycle)


def test_get_crop_lifecycle_unknown_returns_empty():
    """Unknown crop returns empty list."""
    assert get_crop_lifecycle("unknown_crop") == []


def test_get_stage_rules_rice():
    """Stage rules for rice include stages and dependencies."""
    rules = get_stage_rules("rice")
    assert "stages" in rules
    assert "stageNames" in rules
    assert "Sowing" in rules.get("stageNames", [])


def test_get_soil_rules_kolhapur():
    """Kolhapur has regional defaults in default persistent."""
    rules = get_soil_rules("Kolhapur")
    assert "defaults" in rules
    assert rules.get("regional", {}).get("soilType") == "clay"
    assert rules.get("regional", {}).get("ph") == 6.5


def test_get_soil_rules_unknown_region():
    """Unknown region still returns defaults."""
    rules = get_soil_rules("UnknownCity")
    assert "defaults" in rules
    assert "regional" not in rules or rules["regional"] is None


def test_get_crop_catalog():
    """Crop catalog returns list with at least rice."""
    catalog = get_crop_catalog()
    assert isinstance(catalog, list)
    ids = [c.get("id") for c in catalog]
    assert "rice" in ids


def test_get_replanning_rules():
    """Replanning rules include rainBlockedActions and sprayDelayToleranceDays."""
    rules = get_replanning_rules()
    assert "rainBlockedActions" in rules or "replanningRules" in rules
    # Default persistent has replanningRules at top level; get_replanning_rules returns that object
    assert "rainBlockedActions" in rules
    assert "Fungicide spray" in rules.get("rainBlockedActions", [])
