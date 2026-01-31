"""
LangGraph: Plan -> Execute -> Observe -> Re-plan loop.
Conditional: after RiskDetection, if riskEvent -> CalendarReplanner else AdvisoryDelivery.
Feedback -> loop to DailyExecutor (next day) or END.
"""
from __future__ import annotations

from typing import Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state import FarmGraphState, load_variable, save_variable, state_from_variable, variable_from_state, VARIABLE_JSON
from nodes import (
    crop_intent_node,
    context_builder_node,
    crop_calendar_planner_node,
    daily_executor_node,
    weather_observer_node,
    risk_detection_node,
    calendar_replanner_node,
    advisory_delivery_node,
    feedback_node,
)


def route_after_risk(state: FarmGraphState) -> Literal["replanner", "advisory"]:
    """If riskEvent present, go to CalendarReplanner; else AdvisoryDelivery."""
    if state.get("riskEvent"):
        return "replanner"
    return "advisory"


def route_after_feedback(state: FarmGraphState) -> Literal["daily_executor", "end"]:
    """Loop to next day (DailyExecutor) or end. One day per invocation by default."""
    variable = load_variable(VARIABLE_JSON)
    current = variable.get("currentDayIndex", state.get("currentDayIndex", 0))
    calendar = variable.get("cropCalendar") or state.get("cropCalendar") or []
    max_day = max((e.get("day", 0) for e in calendar), default=0)
    if current >= max_day:
        return "end"
    # One day per run; loop would require recursion_limit large enough (e.g. max_day)
    return "end"


def build_farm_graph():
    builder = StateGraph(FarmGraphState)

    builder.add_node("crop_intent", crop_intent_node)
    builder.add_node("context_builder", context_builder_node)
    builder.add_node("crop_calendar_planner", crop_calendar_planner_node)
    builder.add_node("daily_executor", daily_executor_node)
    builder.add_node("weather_observer", weather_observer_node)
    builder.add_node("risk_detection", risk_detection_node)
    builder.add_node("calendar_replanner", calendar_replanner_node)
    builder.add_node("advisory_delivery", advisory_delivery_node)
    builder.add_node("feedback", feedback_node)

    builder.set_entry_point("crop_intent")
    builder.add_edge("crop_intent", "context_builder")
    builder.add_edge("context_builder", "crop_calendar_planner")
    builder.add_edge("crop_calendar_planner", "daily_executor")
    builder.add_edge("daily_executor", "weather_observer")
    builder.add_edge("weather_observer", "risk_detection")
    builder.add_conditional_edges("risk_detection", route_after_risk, {"replanner": "calendar_replanner", "advisory": "advisory_delivery"})
    builder.add_edge("calendar_replanner", "advisory_delivery")
    builder.add_edge("advisory_delivery", "feedback")
    builder.add_conditional_edges("feedback", route_after_feedback, {"daily_executor": "daily_executor", "end": END})

    return builder.compile(checkpointer=MemorySaver())


def run_once(
    crop: str = "rice",
    location: str = "Kolhapur",
    sowing_date: str = "2026-06-15",
    farmer_response: str = "",
    variable_path=None,
):
    """Run graph once: load variable into state, invoke, optionally persist."""
    path = variable_path or VARIABLE_JSON
    variable = load_variable(path)
    variable["crop"] = crop
    variable["location"] = location
    variable["sowingDate"] = sowing_date
    if farmer_response:
        variable["farmer_response"] = farmer_response
    save_variable(variable, path)

    initial: FarmGraphState = state_from_variable(variable)

    graph = build_farm_graph()
    config = {"configurable": {"thread_id": "farm_1"}}
    for event in graph.stream(initial, config):
        pass
    # Final state and persist to variable.json
    final_snapshot = graph.get_state(config)
    final_state = getattr(final_snapshot, "values", None) or initial
    save_variable(variable_from_state(final_state), path)
    return final_state


if __name__ == "__main__":
    import sys
    state = run_once(crop="rice", location="Kolhapur", sowing_date="2026-06-15")
    msg = state.get("message") or "(none)"
    try:
        print("Advisory:", msg)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(("Advisory: " + msg + "\n").encode("utf-8"))
