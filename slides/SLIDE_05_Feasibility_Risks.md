# SLIDE 5 — FEASIBILITY & WHAT IS REAL

## What Is Real (Data and Services Used by the Backend)

All core features are backed by **real APIs and real data** where configured; the system is designed to use authoritative and government-preferred sources.

### Geocoding and Weather

- **Geocoding:** Open-Meteo Geocoding API — resolves city and state (e.g. “Pune, India”) to latitude/longitude; results filtered by country_code IN and optional admin1 (state) match so the location is correct for India.
- **Weather (current):** Open-Meteo Forecast API — current temperature_2m, relative_humidity_2m, and daily precipitation_sum for the resolved coordinates; used in variable generation and as the baseline for calendar regeneration thresholds.
- **Weather (forecast):** Open-Meteo Forecast API — 16-day daily series (temperature_2m_max/min, relative_humidity_2m_mean, precipitation_sum); fetched by the calendar agent and merged into each day’s weather in calendar.json so tasks are planned with real forecast data.

### Soil

- **ISRIC SoilGrids v2:**  
  - **Classification:** WRB soil type and probabilities at the point (variable.json soil_type, soil_map.wrb_class_name).  
  - **Properties:** Clay, sand, silt, SOC, pH (H2O), bulk density, coarse fragments at depths 0–5 cm, 5–15 cm, 15–30 cm; d_factors applied so values are in conventional units (e.g. % for texture, pH, g/kg for SOC).  
  - **Texture class:** USDA texture class derived from clay/sand in the top layer (soil_map.texture_class_usda) for suitability-style use.  
  - **Robustness:** If the exact point returns no data (e.g. urban mask), the backend tries nearby offsets so farmers in peri-urban areas still get soil data.

### Research and Crop Data (Government-Preferred)

- **Tavily Search:** Used by the research agent (disease analysis), crop agent (crop timeline), and market agent (mandi prices). Queries use country=india and results are filtered or preferred for government/educational domains (.gov.in, .nic.in, .ac.in, .icar.org.in) so recommendations and crop timelines are grounded in TNAU, ICAR, state agriculture portals, and similar sources.
- **Research agent (image):** GPT derives a single search query from the image → Tavily search (gov/agri) → second GPT call to synthesize in-depth analysis (identification, causes, evidence-based management), citing the retrieved sources.
- **Crop agent:** Tavily gov-only searches for package of practices, sowing/harvesting months, stages, pesticides, fertilizers; OpenAI extracts a structured CropEntry (Pydantic) with seasons, cycle_duration_days, stages (start_pct, end_pct), pesticides, fertilizers; saved to persistent.json and used by the calendar agent for every calendar generation.

### Market Prices

- **Tavily:** Market agent searches Agmarknet and government agriculture domains (agmarknet.gov.in, agricoop.nic.in, farmer.gov.in) for mandi price content; extracts modal/min/max and date patterns from the text; filters by harvest month; computes average, range, trend (slope from recent prices), and confidence (from data consistency and length). Results cached by crop+state+season for 7 days.

### Crop Recommendation

- **Weather:** Open-Meteo (or OpenWeatherMap when API key is set) for current temperature and humidity at the city.
- **Rainfall:** rainfall_scraper (Open-Meteo or similar) for the location; bucketed (e.g. low/moderate/high) for the AI recommender.
- **News:** Google News RSS for crop/region headlines; signals (e.g. drought, flood, low rainfall) passed to the recommender.
- **OpenAI recommender:** Strict JSON output (crops array, rationale) based on city, soil_type, weather, rainfall, news; prioritizes location-appropriate and soil-suited crops.

### Pest and Disease Risk

- **Data:** variable.json (crop, day_of_cycle, climate) and calendar.json (current stage_name for day_of_cycle).
- **Logic:** Crop-specific PEST_DISEASE_DB (rice, wheat, cotton, tomato, potato) with pests and diseases, their vulnerable stages, humidity/temp ranges, and rainfall_trigger; each pest/disease scored against current weather and stage; overall risk_level (low/medium/high/critical) and risk_score; preventive actions from an IPM-style PREVENTIVE_ACTIONS list. All rule-based and deterministic from real variable and calendar data.
- **Email alerts:** When risk ≥ medium and user provides email, the backend calls the Node email service to send the assessment to the farmer.

### Chatbot

- **Context:** Real variable (location, crop, day_of_cycle, climate, soil), real calendar (today’s tasks, stage, upcoming tasks), real persistent (crop info); on-demand market price prediction and pest risk assessment when the user’s message matches relevant keywords.
- **Model:** GPT-4o; system prompt instructs simple language, government-source citations (TNAU, ICAR, Agmarknet, Open-Meteo, SoilGrids), and actionable advice. Conversation history (last 20 messages per session) keeps dialogue coherent.

---

**Feasibility:** The FastAPI backend is structured so each capability (variable, calendar, crop data, market, pest risk, chat) uses real geocoding, soil, weather, forecast, search, and LLM services. Government and agricultural sources are preferred for crop timeline, disease analysis, and market data where available, making the system suitable for production use with the appropriate API keys and environment configuration.
