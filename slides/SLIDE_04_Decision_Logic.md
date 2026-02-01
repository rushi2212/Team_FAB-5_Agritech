# SLIDE 4 — DECISION LOGIC & ADAPTATION

## Example Decision Flow: Calendar Regeneration

This example shows how the calendar agent decides **when to regenerate** the calendar so the farmer’s daily plan stays aligned with current weather and optional disease insight.

### Inputs

- **variable.json:**  
  - `climate`: temperature_c, humidity_percent, rainfall_mm (current snapshot).  
  - `day_of_cycle`: current day in the crop cycle (1-based).  
  - Also location, crop, soil_type, soil_properties (used in the prompt when regenerating).
- **calendar.json** (if it exists):  
  - `weather_baseline`: climate at the time the calendar was last generated.  
  - `days[]`: each entry has day_index, stage_name, tasks[], and weather for that day.  
  - `start_day`: first day_index in the array (1 for full calendar, or e.g. 5 after a remake from day 5).
- **Environment thresholds** (configurable):  
  - TEMP_THRESHOLD_DEG_C (e.g. 7): max allowed |current temp − baseline temp| for the current day.  
  - HUMIDITY_THRESHOLD_PCT (e.g. 40): max allowed |current humidity − baseline humidity|.  
  - RAIN_THRESHOLD_MM (e.g. 20): max allowed |current rainfall − baseline rainfall|.
- **Optional:** disease_analysis string (from POST /analyze-image → research agent); when present, the calendar should weight disease-management tasks.

### Alternatives

1. **Use existing calendar** — do not call the LLM; keep the current calendar.json as-is. Appropriate when the calendar already exists and current climate for the current day is within thresholds and no new disease_analysis is provided.
2. **Regenerate full calendar** — no existing calendar, or disease_analysis provided: generate days 1 through cycle_duration_days with full 16-day forecast merged into days 1–16, repeat last forecast day for day 17+.
3. **Regenerate from current day onward (remake)** — calendar exists but climate has deviated beyond thresholds: send past days (1 to day_of_cycle−1) to the LLM as context; generate only days day_of_cycle to cycle_duration_days; save only those days (start_day = day_of_cycle) so the farmer sees an updated plan from “today” onward while past days remain as reference in the prompt.

### Why Regeneration Improves the System

- **Weather alignment:** When temperature, humidity, or rainfall have moved beyond thresholds, the existing day-level weather in the calendar no longer matches reality. Regenerating (or remaking) produces tasks and stage assignments consistent with the current and forecast weather (e.g. more irrigation or drainage advice, or pest/disease cues tied to humidity/rain).
- **Disease integration:** When the user uploads an image and gets disease_analysis, passing that into generate-calendar lets the LLM add or emphasize disease-management tasks (scouting, sprays, sanitation) at the right stages, making the calendar actionable for the observed field condition.
- **Continuity on remake:** When remaking from day_of_cycle onward, the prompt includes the past days (1 to day_of_cycle−1) so the model knows what stages and tasks were already planned; the new segment (day_of_cycle to end) stays consistent with the same crop timeline and stages.

### Final Choice (when the agent regenerates)

- **Regenerate (full or from current day)** if:  
  - There is no calendar yet, or  
  - disease_analysis is provided in the request body, or  
  - For the current day_of_cycle, the current climate (variable.climate) deviates from that day’s weather in calendar.days beyond any of the three thresholds (temp, humidity, rain).
- **Use existing calendar** when a calendar exists, no disease_analysis is provided, and current climate for the current day is within all thresholds — so the plan is still valid and no LLM call is needed.

### What Happens When Inputs Change

- **User advances day_of_cycle (PATCH /variable):** The next POST /generate-calendar loads the updated variable. The current day used for threshold comparison is the new day_of_cycle; if the climate for that day in the calendar differs from variable.climate beyond thresholds, the agent regenerates (typically a remake from that day onward).
- **User refreshes location/crop/weather (POST /generate-variable):** variable.json is rewritten with new climate. The next POST /generate-calendar compares this new climate to the existing calendar’s weather for the current day_of_cycle; if beyond thresholds, the agent regenerates so the calendar reflects the updated conditions.
- **User uploads an image and gets disease_analysis (POST /analyze-image), then calls POST /generate-calendar with that analysis in the body:** The agent always regenerates so the new calendar incorporates disease-management emphasis from the image-based analysis.
