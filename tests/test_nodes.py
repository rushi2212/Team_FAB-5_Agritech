"""
Unit tests for each LangGraph node with fixed state/variable and patched paths.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def _patch_paths(patch_data_paths):
    """Use temp data dir for all node tests."""
    pass


def test_crop_intent_node_valid(sample_state, patch_data_paths):
    """CropIntentNode with valid rice + Kolhapur returns crop and location."""
    from nodes.crop_intent_node import crop_intent_node
    out = crop_intent_node(sample_state)
    assert out["crop"] == "rice"
    assert out["location"] == "Kolhapur"
    assert "crop_catalog" in (out.get("knowledgeSourcesUsed") or [])


def test_context_builder_node(sample_state, patch_data_paths):
    """ContextBuilderNode sets soilContext and weatherForecast."""
    from nodes.context_builder_node import context_builder_node
    sample_state["location"] = "Kolhapur"
    out = context_builder_node(sample_state)
    assert "soilContext" in out
    assert out["soilContext"].get("type") == "clay"
    assert "weatherForecast" in out
    # Variable.json should be updated
    path = patch_data_paths["variable_json"]
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "soilContext" in data


def test_crop_calendar_planner_node(sample_state, patch_data_paths):
    """CropCalendarPlannerNode produces non-empty calendar and writes to variable."""
    from nodes.crop_calendar_planner_node import crop_calendar_planner_node
    sample_state["soilContext"] = {"type": "clay", "ph": 6.5}
    sample_state["expectedWeatherPattern"] = "monsoon"
    out = crop_calendar_planner_node(sample_state)
    assert len(out["cropCalendar"]) >= 1
    assert out["currentDayIndex"] == 0
    assert out["currentCropStage"] == "Sowing"
    data = json.loads(patch_data_paths["variable_json"].read_text(encoding="utf-8"))
    assert len(data["cropCalendar"]) >= 1


def test_daily_executor_node(sample_state, patch_data_paths, sample_variable):
    """DailyExecutorNode returns todayActions for currentDayIndex."""
    path = patch_data_paths["variable_json"]
    path.write_text(json.dumps(sample_variable, indent=2), encoding="utf-8")
    from nodes.daily_executor_node import daily_executor_node
    state = {**sample_state, "currentDayIndex": 1, "cropCalendar": sample_variable["cropCalendar"]}
    out = daily_executor_node(state)
    assert "todayActions" in out
    assert "Seed soaking" in out["todayActions"] or "Field puddling" in out["todayActions"]


def test_weather_observer_clear(sample_state, patch_data_paths):
    """WeatherObserverNode sets CLEAR when no rain (uses patched paths)."""
    from nodes.weather_observer_node import weather_observer_node
    out = weather_observer_node(sample_state)
    assert out["weatherRisk"] == "CLEAR"


def test_weather_observer_rain(sample_state, patch_data_paths):
    """WeatherObserverNode sets RAIN_EXPECTED when rain_probability >= 70."""
    path = patch_data_paths["variable_json"]
    data = json.loads(path.read_text(encoding="utf-8"))
    data["weatherForecast"] = {"rain_probability": 80}
    path.write_text(json.dumps(data), encoding="utf-8")
    from nodes.weather_observer_node import weather_observer_node
    out = weather_observer_node({**sample_state, "weatherForecast": {"rain_probability": 80}})
    assert out["weatherRisk"] == "RAIN_EXPECTED"


def test_risk_detection_no_risk(sample_state, patch_data_paths):
    """RiskDetectionNode sets riskEvent None when weather clear (uses patched paths)."""
    sample_state["todayActions"] = ["Seed soaking"]
    sample_state["weatherRisk"] = "CLEAR"
    from nodes.risk_detection_node import risk_detection_node
    out = risk_detection_node(sample_state)
    assert out["riskEvent"] is None


def test_risk_detection_rain_blocks_spray(sample_state, patch_data_paths):
    """RiskDetectionNode sets ACTION_BLOCKED when rain and Fungicide spray in todayActions (uses patched paths)."""
    sample_state["todayActions"] = ["Fungicide spray"]
    sample_state["weatherRisk"] = "RAIN_EXPECTED"
    from nodes.risk_detection_node import risk_detection_node
    out = risk_detection_node(sample_state)
    assert out["riskEvent"] is not None
    assert out["riskEvent"]["type"] == "ACTION_BLOCKED"
    assert "Rain" in out["riskEvent"].get("reason", "")


def test_advisory_delivery_no_actions(sample_state, patch_data_paths):
    """AdvisoryDeliveryNode returns monitoring message when no todayActions."""
    sample_state["todayActions"] = []
    sample_state["riskEvent"] = None
    from nodes.advisory_delivery_node import advisory_delivery_node
    out = advisory_delivery_node(sample_state)
    assert "message" in out
    assert "निरीक्षण" in out["message"] or "कृती" in out["message"]


def test_advisory_delivery_rain(sample_state, patch_data_paths):
    """AdvisoryDeliveryNode returns do-not-spray message when riskEvent Rain."""
    sample_state["todayActions"] = ["Fungicide spray"]
    sample_state["riskEvent"] = {"type": "ACTION_BLOCKED", "reason": "Rain"}
    from nodes.advisory_delivery_node import advisory_delivery_node
    out = advisory_delivery_node(sample_state)
    assert "message" in out
    assert "फवारणी" in out["message"] or "पाऊस" in out["message"]


def test_feedback_node_increments_day(sample_state, patch_data_paths, sample_variable):
    """FeedbackNode increments currentDayIndex and updates variable.json."""
    path = patch_data_paths["variable_json"]
    sample_variable["currentDayIndex"] = 5
    path.write_text(json.dumps(sample_variable), encoding="utf-8")
    from nodes.feedback_node import feedback_node
    state = {**sample_state, "todayActions": ["Seed soaking"], "riskEvent": None}
    out = feedback_node(state)
    assert out["currentDayIndex"] == 6
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["currentDayIndex"] == 6
