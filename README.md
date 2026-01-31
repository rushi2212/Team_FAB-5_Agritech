git # LangGraph Crop Calendar

Plan → Execute → Observe → Re-plan loop for a stage-wise, day-wise crop action calendar. Uses **variable.json** (per-day state) and **persistent.json** (rules and static knowledge).

## Data model

- **data/variable.json** – Daily/variable state: weather, currentDayIndex, cropCalendar, completed/skipped/delayed actions, risk events. Updated each run.
- **data/persistent.json** – Rules: crop catalog, stage models, soil rules, replanning rules. Read by planner and replanner.

## Run

```bash
pip install -r requirements.txt
python graph.py
```

Optional args (edit `graph.py` `__main__`): `crop`, `location`, `sowing_date`, `farmer_response`.

## Graph

1. **CropIntentNode** – Validate crop/location from persistent catalog.
2. **ContextBuilderNode** – Build soilContext, weatherForecast from persistent + variable.
3. **CropCalendarPlannerNode** – Build full calendar till harvest; write to variable.json.
4. **DailyExecutorNode** – Pick today’s actions from calendar.
5. **WeatherObserverNode** – Set weatherRisk (e.g. RAIN_EXPECTED).
6. **RiskDetectionNode** – Set riskEvent if action blocked (e.g. rain); write to variable.
7. **CalendarReplannerNode** – Reschedule blocked actions; write updated calendar to variable (only when risk).
8. **AdvisoryDeliveryNode** – Build message (e.g. Marathi); optional write last_advisory.
9. **FeedbackNode** – Update currentDayIndex, completed/skipped/delayed; write variable.

Conditional: after RiskDetection, if `riskEvent` → CalendarReplanner else AdvisoryDelivery. After Feedback → end (one day per invocation).
