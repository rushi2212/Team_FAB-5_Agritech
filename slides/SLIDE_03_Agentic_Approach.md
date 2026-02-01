# SLIDE 3 — AGENTIC TECHNICAL APPROACH

## Simple Architecture: Inputs → Agent → Decision → Action

**Inputs** (state/city/crop/season, image upload, city+soil, user message, optional user_email)  
→ **Agents** (Variable generation, Research agent, Calendar agent, Crop agent, Market agent, Pest agent, Chatbot)  
→ **Decisions** (what to compute, when to regenerate, when to fetch, when to cache, when to alert)  
→ **Actions** (variable.json, calendar.json, persistent.json, disease analysis text, price prediction, risk assessment, chat response)

### Per-agent flow

- **Variable generation:** Input = state, city, crop_name, season. Action = geocode → fetch soil (SoilGrids classification + properties by depth) → fetch weather (Open-Meteo) → write variable.json. No decision step; always produces one variable per request.
- **Research agent:** Input = image (or text). Action = GPT to derive search query → Tavily search (government/agri domains: .gov.in, .nic.in, .ac.in, .icar.org.in) → second GPT call to synthesize in-depth disease analysis (identification, causes, evidence-based management). Optional tool-calling loop for text/text+image queries.
- **Calendar agent:** Input = variable + persistent + optional disease_analysis. Decision = should_regenerate (no calendar, or disease_analysis present, or current climate vs baseline exceeds thresholds). Action = ensure crop in persistent → fetch 16-day forecast → build prompt (with past days if remake) → OpenAI reasoning → parse days → merge forecast into each day → save calendar.json.
- **Crop agent:** Input = crop_name, state, season (from calendar agent). Decision = crop+state in persistent? If not, action = Tavily gov-only searches (package of practices, sowing/harvesting, stages, pesticides, fertilizers) → OpenAI extraction to CropEntry (Pydantic) → save to persistent.json.
- **Market agent:** Input = crop, state, season, harvest_month. Decision = cache hit and &lt; 7 days old? If not, action = Tavily search (Agmarknet, agricoop.nic.in, farmer.gov.in) or historical query → extract prices → filter by harvest month → compute avg/min/max and trend/confidence → cache and return.
- **Pest agent:** Input = variable + calendar + optional user_email. Action = load variable (crop, day_of_cycle, climate) and calendar (current stage) → score each pest/disease in DB against stage and weather → aggregate risk_level and risk_score → attach preventive_actions → if risk ≥ medium and user_email, POST to Node email service → cache result and return.
- **Chatbot:** Input = message, session_id. Decision = which context to add (from keywords: price/market → get_price_prediction; pest/disease → assess_pest_disease_risk; calendar/upcoming → upcoming tasks; fertilizer/stage → persistent crop info). Action = build prompt with context + last 10 messages → GPT-4o → extract cited sources → append to history (last 20) → return response + suggestions.

## Planning

The **calendar agent** performs explicit planning over the crop cycle: it produces a full sequence of day_index values from 1 to cycle_duration_days (or from current day onward on a remake), each with a stage_name (from persistent stages and percentage-of-cycle timing) and a list of detailed tasks. The prompt includes location, crop, soil, climate snapshot, crop timeline (stages, pesticides, fertilizers, sowing/harvesting months), and the 16-day forecast; when remaking from a given day, it also sends the past days (1 to day_of_cycle−1) as context so the model maintains continuity. The model is instructed to output only day_index (no calendar dates), making the plan portable and weather-driven.

## Memory (even basic)

- **variable.json:** Single source of truth for location, crop, day_of_cycle, soil (type, map, properties by depth), and climate; read by calendar agent, pest agent, and chatbot.
- **persistent.json:** Crop timeline data keyed by crop_state (e.g. rice_maharashtra): seasons, sowing/harvesting months, cycle_duration_days, stages (name, start_pct, end_pct, description), pesticides, fertilizers; written by crop agent, read by calendar agent and chatbot.
- **calendar.json:** weather_baseline, cycle_duration_days, start_day, location, crop, forecast_snapshot, and days[] (day_index, stage_name, tasks[], weather per day); written by calendar agent, read by pest agent (for current stage) and chatbot (for today’s tasks and upcoming).
- **Chatbot:** In-memory conversation history per session_id (last 20 messages); used to maintain dialogue context for each user.
- **Market agent:** File cache in agents/data/market_prices.json keyed by crop_state_season; 7-day validity so repeated requests are fast.
- **Pest agent:** Last assessment written to agents/data/pest_disease_risk.json for inspection or reuse.

## Adaptation Trigger

- **Calendar:** Regeneration is triggered when (1) no calendar exists, (2) disease_analysis is provided (so new disease insight is reflected), or (3) current climate for the current day_of_cycle deviates from that day’s weather in the existing calendar beyond env thresholds (e.g. TEMP 7°C, HUMIDITY 40%, RAIN 20 mm). This keeps the plan aligned with real weather without regenerating on every request.
- **Crop data:** Fetch and save to persistent when the crop+state key is missing, so the calendar agent always has stages, pesticides, and fertilizers for the selected crop and region.
- **Market cache:** Refresh after 7 days so price predictions stay reasonably current while avoiding redundant Tavily calls.
