# LangGraph Crop Calendar — In-Depth Documentation

This document covers architecture, data model, node behavior, graph flow, setup, and **testing** (unit, integration, and manual scenarios) in detail.

---

## Table of Contents

1. [Overview and Architecture](#1-overview-and-architecture)
2. [Data Model](#2-data-model)
3. [Node-by-Node Reference](#3-node-by-node-reference)
4. [Graph Flow and Conditional Edges](#4-graph-flow-and-conditional-edges)
5. [Setup and Installation](#5-setup-and-installation)
6. [Testing](#6-testing)
7. [Manual Test Scenarios](#7-manual-test-scenarios)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Overview and Architecture

### Core concept

Generate a **stage-wise, day-wise crop action calendar**, then **re-plan** when real-world events (rain, heatwave, farmer skip) block planned actions. This is a **Plan → Execute → Observe → Re-plan** loop.

### Two levels of intelligence

| Level | Node(s) | Role |
|-------|---------|------|
| **Strategic** | CropCalendarPlannerNode | Build full calendar till harvest (once, or on major replan) |
| **Tactical** | CalendarReplannerNode | Adjust remaining calendar when a risk event occurs (e.g. rain) |

### Data stores

- **persistent.json** — Rules and static knowledge (crop catalog, stage models, soil rules, replanning rules). **Read-only** by planner and replanner.
- **variable.json** — Per-day and cumulative variable state (calendar, current day, actions, risks). **Read/write** by multiple nodes.

### File layout

```
Hackathon/
├── state.py              # FarmGraphState, load/save variable.json and persistent.json
├── graph.py              # LangGraph build, run_once(), entrypoint
├── requirements.txt
├── data/
│   ├── persistent.json   # Rules (crop catalog, stage models, soil, replanning)
│   └── variable.json      # Variable state (calendar, current day, actions, risks)
├── knowledge/
│   ├── __init__.py
│   └── loaders.py        # get_crop_lifecycle, get_stage_rules, get_soil_rules, get_replanning_rules
├── nodes/
│   ├── crop_intent_node.py
│   ├── context_builder_node.py
│   ├── crop_calendar_planner_node.py
│   ├── daily_executor_node.py
│   ├── weather_observer_node.py
│   ├── risk_detection_node.py
│   ├── calendar_replanner_node.py
│   ├── advisory_delivery_node.py
│   └── feedback_node.py
├── tests/
│   ├── conftest.py       # Pytest fixtures (paths, state, variable, persistent)
│   ├── test_state.py     # Unit tests for state load/save and conversion
│   ├── test_knowledge.py  # Unit tests for knowledge loaders
│   ├── test_nodes.py     # Unit tests for each node
│   └── test_graph.py     # Integration tests for full graph
├── DOCUMENTATION.md      # This file
└── README.md
```

---

## 2. Data Model

### 2.1 `data/persistent.json` (rules; read-only in normal flow)

| Section | Purpose | Used by |
|---------|---------|---------|
| `cropCatalog` | Crop id, name, suitableRegions, season, typicalDurationDays | CropIntentNode |
| `stageModels.<crop>` | Per-stage: stage, dayStart, dayEnd, actions, dependencies, weatherConstraints | CropCalendarPlannerNode |
| `soilRules.defaults` | Soil type → ph_range, nitrogen_advice | ContextBuilderNode |
| `soilRules.regionalDefaults` | Location → soilType, ph | ContextBuilderNode |
| `replanningRules` | sprayDelayToleranceDays, rainBlockedActions, alternativeActions, weatherWindows | RiskDetectionNode, CalendarReplannerNode |

**Example snippet (rice stages):**

```json
"stageModels": {
  "rice": [
    { "stage": "Sowing", "dayStart": 1, "dayEnd": 7, "actions": ["Seed soaking", "Field puddling", "Transplanting"], ... },
    { "stage": "Tillering", "dayStart": 8, "dayEnd": 35, "actions": ["First nitrogen application", "Weeding", "Water management"], ... },
    { "stage": "Protection", "dayStart": 36, "dayEnd": 60, "actions": ["Fungicide spray", "Pest monitoring", ...], ... }
  ]
}
```

### 2.2 `data/variable.json` (variable state; read/write)

| Field | Type | Written by | Description |
|-------|------|------------|-------------|
| `location`, `crop`, `sowingDate` | string | run_once / ContextBuilder / Planner | Farmer context |
| `soilContext` | object | ContextBuilderNode | type, ph, advice |
| `weatherForecast` | object | ContextBuilderNode | 15_day, expectedPattern, rain_probability |
| `weatherHistory` | array | ContextBuilderNode | Historical weather |
| `cropCalendar` | array of CalendarEntry | CropCalendarPlannerNode, CalendarReplannerNode | Master plan (day, stage, actions, dependencies, weatherConstraints) |
| `currentDayIndex` | int | CropCalendarPlannerNode (init), FeedbackNode (increment) | Current day in crop lifecycle |
| `currentCropStage` | string | CropCalendarPlannerNode, DailyExecutorNode | Current stage name |
| `todayActions` | array | (in-memory from DailyExecutorNode; not stored long-term) | Actions for today |
| `weatherRisk` | string | WeatherObserverNode | RAIN_EXPECTED, HEATWAVE, CLEAR |
| `riskEvent` | object or null | RiskDetectionNode | type (e.g. ACTION_BLOCKED), reason (e.g. Rain) |
| `riskEvents` | array | RiskDetectionNode | History of risk events |
| `completedActions`, `skippedActions`, `delayedActions` | array | FeedbackNode | Execution history |
| `confidenceScores` | object | FeedbackNode | Optional confidence metrics |
| `last_advisory` | string | AdvisoryDeliveryNode | Last message shown to farmer |
| `farmer_response` | string | (input) | did_not_spray, completed, etc. |

### 2.3 In-memory state (`FarmGraphState`)

The graph passes a single state object between nodes. It includes all of the variable fields above plus transient fields like `todayActions`, `weatherRisk`, `riskEvent`, `message`. See `state.py` for the full `FarmGraphState` TypedDict.

---

## 3. Node-by-Node Reference

### Node 1: CropIntentNode

- **Purpose:** Validate crop and location against the catalog.
- **Inputs (from state):** `crop`, `location`, `sowingDate`.
- **Knowledge:** `persistent.json` → `cropCatalog` (crop id, suitableRegions).
- **Output:** `crop`, `location`, `sowingDate`, `knowledgeSourcesUsed` (appends `crop_catalog`, `regional_suitability`).
- **Writes variable.json:** No.

**Validation logic:** Crop must exist in catalog; if the crop has `suitableRegions`, location must be in that list (or validation passes if no regions defined).

---

### Node 2: ContextBuilderNode

- **Purpose:** Build soil and weather context for planning.
- **Inputs:** State from CropIntentNode; reads `variable.json` for weather history / last day.
- **Knowledge:** `persistent.json` → `soilRules` (defaults, regionalDefaults).
- **Output:** `soilContext` (type, ph, advice), `weatherForecast`, `weatherHistory`, `expectedWeatherPattern`.
- **Writes variable.json:** Yes — `weatherForecast`, `weatherHistory`, `soilContext`.

---

### Node 3: CropCalendarPlannerNode

- **Purpose:** Build the full crop calendar till harvest (strategic plan).
- **Inputs:** `crop`, `sowingDate`, `soilContext`, `expectedWeatherPattern`; optionally existing `cropCalendar` from variable (for major replan).
- **Knowledge:** `persistent.json` → `stageModels.<crop>` (stage, dayStart, actions, dependencies, weatherConstraints).
- **Output:** `cropCalendar` (list of CalendarEntry), `currentDayIndex` (0), `currentCropStage` (first stage), `knowledgeSourcesUsed`.
- **Writes variable.json:** Yes — `cropCalendar`, `currentDayIndex`, `currentCropStage`, plus crop/sowingDate/location/soilContext.

---

### Node 4: DailyExecutorNode

- **Purpose:** Pick today’s actions from the calendar.
- **Inputs:** `variable.json` → `currentDayIndex`, `cropCalendar`; state can override.
- **Output:** `todayActions` (list of action strings), `currentCropStage`.
- **Writes variable.json:** No. Read-only on calendar.

**Logic:** Finds calendar entries where `day == currentDayIndex`; aggregates their `actions`. If no entry for that day, only `currentCropStage` is set from the latest stage that has started.

---

### Node 5: WeatherObserverNode

- **Purpose:** Derive weather risk from forecast.
- **Inputs:** `variable.json` / state → `weatherForecast` (e.g. `rain_probability`, `rainProbability`, `heatwave`).
- **Output:** `weatherRisk` — `RAIN_EXPECTED` (rain_prob ≥ 70), `HEATWAVE`, or `CLEAR`.
- **Writes variable.json:** Yes — `weatherRisk`.

---

### Node 6: RiskDetectionNode

- **Purpose:** Detect if today’s action is blocked by weather (e.g. spray in rain).
- **Inputs:** `todayActions`, `weatherRisk`; optionally `farmer_response` from variable.
- **Knowledge:** `persistent.json` → `replanningRules.rainBlockedActions`.
- **Output:** `riskEvent` (e.g. `{ "type": "ACTION_BLOCKED", "reason": "Rain" }` or null), `riskEvents` (append).
- **Writes variable.json:** Yes — `riskEvent`, `riskEvents`.

**Logic:** If `weatherRisk == "RAIN_EXPECTED"` and any of today’s actions matches `rainBlockedActions`, set `riskEvent`. If `weatherRisk == "HEATWAVE"`, set heat stress risk.

---

### Node 7: CalendarReplannerNode

- **Purpose:** Reschedule blocked actions (tactical re-plan).
- **Inputs:** `riskEvent`, `todayActions`, `variable.json` → `currentDayIndex`, `cropCalendar`.
- **Knowledge:** `persistent.json` → `replanningRules` (sprayDelayToleranceDays, etc.).
- **Output:** `cropCalendar` (updated).
- **Writes variable.json:** Yes — full updated `cropCalendar`.

**Logic:** Only runs when `riskEvent` is set. Splits calendar into past and remaining (from `currentDayIndex`). For the entry at `current_day` with reason "Rain", moves blocked actions to a reschedule day (current_day + 2, capped by max_delay); adds a “today” entry with non-blocked actions or "Field scouting". Merges past + updated remaining and saves.

---

### Node 8: AdvisoryDeliveryNode

- **Purpose:** Produce the farmer-facing message (e.g. Marathi).
- **Inputs:** `todayActions`, `riskEvent`.
- **Output:** `message` (string).
- **Writes variable.json:** Yes — `last_advisory`.

**Message rules:** If `riskEvent.type == "ACTION_BLOCKED"` and reason Rain → fixed Marathi “do not spray today, rain expected”. Else if `todayActions` non-empty → “आज करावयाच्या कृती: …”. Else → “आज विशिष्ट कृती नाही. शेताचे निरीक्षण करा.”

---

### Node 9: FeedbackNode

- **Purpose:** Record execution outcome and advance the day.
- **Inputs:** `farmer_response`, `todayActions`, `riskEvent`; `variable.json` → current lists and currentDayIndex.
- **Output:** `currentDayIndex` (incremented), `completedActions`, `skippedActions`, `delayedActions`, `confidenceScores`.
- **Writes variable.json:** Yes — all of the above; clears `riskEvent` for next run.

**Logic:** If farmer_response is "did_not_spray" or risk was ACTION_BLOCKED → append today’s actions to `skippedActions`. If "completed" → append to `completedActions`. Else → append to `delayedActions`. Then `currentDayIndex += 1`.

---

## 4. Graph Flow and Conditional Edges

### Linear segment

```
START → crop_intent → context_builder → crop_calendar_planner → daily_executor → weather_observer → risk_detection
```

### Conditional after risk_detection

- If `state.riskEvent` is set → **calendar_replanner** → advisory_delivery → feedback.
- Else → **advisory_delivery** → feedback.

### After feedback

- Currently always → **END** (one day per invocation). The design allows a branch to `daily_executor` to loop “next day” (would require a higher `recursion_limit`).

### Summary

- One run = **one day** of the plan: intent → context → (optional first-time or major) plan → get today’s actions → weather → risk → (optional replan) → advisory → feedback → persist and end.
- Persistence: nodes that need to persist read/write `variable.json`; `run_once()` also saves the final state to `variable.json` at the end.

---

## 5. Setup and Installation

### Requirements

- Python 3.10+ (3.12 recommended).
- Dependencies: `langgraph`, `langchain-core` (see `requirements.txt`).

### Install

```bash
cd C:\Users\Lenovo\Desktop\Hackathon
pip install -r requirements.txt
```

### Run one full day

```bash
python graph.py
```

This uses default `crop="rice"`, `location="Kolhapur"`, `sowing_date="2026-06-15"`. The advisory is printed (UTF-8); on Windows, if the console does not support Marathi, the fallback writes UTF-8 bytes to stdout.

### Programmatic run

```python
from graph import run_once

state = run_once(
    crop="rice",
    location="Kolhapur",
    sowing_date="2026-06-15",
    farmer_response="",  # or "completed" / "did_not_spray"
)
print(state.get("message"))
print(state.get("cropCalendar"))
```

Optional: pass `variable_path=Path("tests/fixtures/variable.json")` to use a test variable file.

---

## 6. Testing

### 6.1 Test layout

- **tests/conftest.py** — Fixtures: paths to test `data/`, in-memory `variable` and `persistent` dicts, sample `FarmGraphState`.
- **tests/test_state.py** — Unit tests for `load_variable`, `save_variable`, `load_persistent`, `state_from_variable`, `variable_from_state`.
- **tests/test_knowledge.py** — Unit tests for `get_crop_lifecycle`, `get_stage_rules`, `get_soil_rules`, `get_crop_catalog`, `get_replanning_rules`.
- **tests/test_nodes.py** — Unit tests for each node with fixed state/variable/persistent (and temp files where needed).
- **tests/test_graph.py** — Integration tests: run full graph with test data and assert final state and variable.json contents.

### 6.2 Running tests

```bash
cd C:\Users\Lenovo\Desktop\Hackathon
pip install -r requirements.txt   # includes pytest
pytest tests/ -v
```

All 25 tests use a temp data dir and monkeypatch `state.VARIABLE_JSON` and `state.PERSISTENT_JSON` (and `knowledge.loaders._DEFAULT_PERSISTENT`) so production `data/` is not modified. Nodes use `state_module.VARIABLE_JSON` at runtime so the patch applies.

Run a single file or test:

```bash
pytest tests/test_state.py -v
pytest tests/test_nodes.py -v -k "crop_intent"
pytest tests/test_graph.py -v
```

### 6.3 What to test (checklist)

| Area | What to verify |
|------|----------------|
| **State** | Load/save variable and persistent; state_from_variable and variable_from_state round-trip; missing file → empty dict. |
| **Knowledge** | get_crop_lifecycle("rice") returns stages; get_soil_rules("Kolhapur") returns regional + defaults; get_replanning_rules() returns rainBlockedActions etc. |
| **CropIntent** | Valid crop+region → crop and location in output; invalid crop or wrong region → still returns crop/location (validation is per-catalog; you can assert catalog content). |
| **ContextBuilder** | soilContext has type, ph; weatherForecast present; variable.json updated. |
| **CropCalendarPlanner** | cropCalendar has entries for each stage; currentDayIndex 0; variable.json has calendar. |
| **DailyExecutor** | For currentDayIndex 1 → todayActions = Sowing actions; for 0 → todayActions = [] and currentCropStage set. |
| **WeatherObserver** | rain_probability >= 70 → RAIN_EXPECTED; else CLEAR; variable.json has weatherRisk. |
| **RiskDetection** | RAIN_EXPECTED + Fungicide spray in todayActions → riskEvent ACTION_BLOCKED; variable.json updated. |
| **CalendarReplanner** | When riskEvent is Rain, remaining calendar has rescheduled entry and “Field scouting” for today; variable.json updated. |
| **AdvisoryDelivery** | riskEvent Rain → Marathi “do not spray”; no risk and todayActions → “आज करावयाच्या कृती: …”; else “no specific action”. |
| **Feedback** | currentDayIndex increments; completed/skipped/delayed updated per farmer_response/risk; variable.json updated. |
| **Graph** | run_once with default args → message present; variable.json has cropCalendar, currentDayIndex, last_advisory. |

### 6.4 Unit test examples (conceptual)

**State:**

- Create a temp directory and `variable.json` with `{"crop":"rice","currentDayIndex":1}`. Load and assert keys. Save and re-load and assert.
- Call `state_from_variable(variable)` then `variable_from_state(state)` and assert critical keys match.

**Knowledge:**

- With `persistent.json` in `data/`, call `get_crop_lifecycle("rice")` and assert length and first stage name.
- Call `get_soil_rules("Kolhapur")` and assert `regional` and `defaults` present.

**Nodes:**

- CropIntent: state `{ "crop": "rice", "location": "Kolhapur" }` → run `crop_intent_node(state)` → assert `"crop" in result` and `"rice" in result.get("crop","")`.
- DailyExecutor: set variable (or state) with `currentDayIndex: 1`, `cropCalendar: [{ "day": 1, "stage": "Sowing", "actions": ["Seed soaking"] }]` → run `daily_executor_node(state)` → assert `result["todayActions"] == ["Seed soaking"]`.
- RiskDetection: state `todayActions: ["Fungicide spray"]`, `weatherRisk: "RAIN_EXPECTED"` → run with temp variable path → assert `result["riskEvent"]["type"] == "ACTION_BLOCKED"`.

### 6.5 Integration test (conceptual)

- Copy `data/persistent.json` to a test data dir (or use existing). Start with empty or minimal `variable.json` (e.g. only crop, location, sowingDate).
- Call `run_once(crop="rice", location="Kolhapur", sowing_date="2026-06-15", variable_path=test_variable_path)`.
- Load `variable_path` and assert: `cropCalendar` non-empty, `currentDayIndex` >= 0, `last_advisory` non-empty, `soilContext` present.

---

## 7. Manual Test Scenarios

### Scenario A: First run (calendar creation + day 0)

1. Ensure `data/variable.json` is empty or has only `crop`, `location`, `sowingDate`.
2. Run `python graph.py`.
3. **Expect:** `data/variable.json` contains full `cropCalendar` (e.g. 5 entries for rice), `currentDayIndex` 1 (after feedback), `soilContext` (e.g. Kolhapur → clay, ph 6.5), `last_advisory` (e.g. “आज विशिष्ट कृती नाही…” for day 0).
4. Console shows one advisory line.

### Scenario B: Rain blocks spray (replan)

1. Set `data/variable.json` so that **today** is a spray day: e.g. `currentDayIndex: 36`, and keep the existing rice `cropCalendar` (day 36 = Protection, Fungicide spray).
2. Set `weatherForecast` to trigger rain: e.g. `"rain_probability": 80` or `"rainProbability": 80`.
3. Run `python graph.py` (same crop/location/sowing_date).
4. **Expect:** `riskEvent`: `{ "type": "ACTION_BLOCKED", "reason": "Rain" }`; CalendarReplanner runs; `cropCalendar` has an entry for current day with “Field scouting” and a later day with “Fungicide spray (rescheduled)”; advisory is the Marathi “do not spray today, rain expected” message.

### Scenario C: Clear day with actions

1. Set `currentDayIndex: 1` and ensure `cropCalendar` has day 1 (Sowing actions).
2. Set `weatherForecast: {}` or `rain_probability: 0` so WeatherObserver sets `weatherRisk: "CLEAR"`.
3. Run `python graph.py`.
4. **Expect:** No riskEvent; advisory lists today’s actions (e.g. Seed soaking, Field puddling, Transplanting); FeedbackNode appends to completed/skipped/delayed per `farmer_response` and increments `currentDayIndex` to 2.

### Scenario D: Wheat and different region

1. Add wheat to `persistent.json` `cropCatalog` and `stageModels` if not present (already present in default persistent).
2. Run with `crop="wheat"`, `location="Kolhapur"` (or another suitable region from catalog).
3. **Expect:** ContextBuilder and CropCalendarPlanner use wheat stages; calendar and advisories reflect wheat lifecycle.

### Scenario E: Invalid crop or region

1. Run with `crop="unknown"` or `location="UnknownCity"` (not in catalog’s suitableRegions).
2. **Expect:** CropIntentNode still returns the given crop/location (validation is catalog-based; you can assert in tests that for invalid input, downstream nodes may produce empty calendar or you can extend CropIntent to set a `valid` flag and branch).

---

## 8. Troubleshooting

| Issue | What to check |
|-------|----------------|
| **ModuleNotFoundError: state / nodes / knowledge** | Run from project root: `C:\Users\Lenovo\Desktop\Hackathon`. Do not run from `nodes/` or `knowledge/`. |
| **variable.json or persistent.json not found** | Ensure `data/` exists and contains `variable.json` and `persistent.json`. `state.py` and `knowledge/loaders.py` resolve paths relative to the project root. |
| **Empty cropCalendar** | Ensure `persistent.json` has `stageModels.<crop>` for your crop (e.g. `stageModels.rice`). Crop name in state must match (e.g. `"rice"`). |
| **No advisory / wrong language** | Advisory is built in AdvisoryDeliveryNode (Marathi for rain; action list otherwise). If console garbles script, use UTF-8: `PYTHONIOENCODING=utf-8` or the built-in UTF-8 fallback in `graph.py`. |
| **Recursion limit (if you enable daily loop)** | If you change `route_after_feedback` to return `"daily_executor"`, increase `recursion_limit` in config, e.g. `graph.stream(initial, { **config, "recursion_limit": 150 })`. |
| **Tests fail on paths** | Tests should use fixtures in `tests/fixtures/` or temp directories; `conftest.py` can override `VARIABLE_JSON` and `PERSISTENT_JSON` via env or fixture so production `data/` is not overwritten. |

---

## Quick reference: persistence by node

| Node | Reads variable.json | Writes variable.json |
|------|---------------------|------------------------|
| CropIntentNode | No | No |
| ContextBuilderNode | Yes (weather, etc.) | Yes (soilContext, weatherForecast, weatherHistory) |
| CropCalendarPlannerNode | Yes (optional existing calendar) | Yes (cropCalendar, currentDayIndex, currentCropStage, crop, sowingDate, location, soilContext) |
| DailyExecutorNode | Yes (currentDayIndex, cropCalendar) | No |
| WeatherObserverNode | Yes (weatherForecast) | Yes (weatherRisk) |
| RiskDetectionNode | Yes | Yes (riskEvent, riskEvents) |
| CalendarReplannerNode | Yes (currentDayIndex, cropCalendar, riskEvent) | Yes (cropCalendar) |
| AdvisoryDeliveryNode | Yes | Yes (last_advisory) |
| FeedbackNode | Yes (currentDayIndex, lists, farmer_response) | Yes (currentDayIndex, completed/skipped/delayed, confidenceScores, clear riskEvent) |
