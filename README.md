# Crop Calendar & Farming Assistant

**Team FAB-5** — Agritech

A full-stack farming assistant that generates location- and crop-specific daily calendars, recommends crops, predicts harvest-time market prices, assesses pest and disease risk, and provides a conversational assistant with government-source citations. Includes LLM-based safety checks to flag hazardous content in calendar tasks.

---

## Features

- **Farm context (variable)** — Generate `variable.json` from state, city, crop, and season using geocoding (Open-Meteo), soil (ISRIC SoilGrids), and weather (Open-Meteo).
- **Day-by-day crop calendar** — Build or update a calendar from variable + persistent crop data and a 16-day forecast; optional disease analysis from images to weight disease-management tasks.
- **Crop recommendation** — City + soil + weather + rainfall + news → AI recommender (OpenAI) returns up to three crops and rationale.
- **Market price prediction** — Harvest-time price prediction from Agmarknet/gov sources (Tavily) or fallback; trend and confidence; 7-day cache.
- **Pest & disease risk** — Rule-based risk from crop stage and weather; preventive actions; optional email alerts (Node service).
- **Calendar hazard scan** — LLM analyzes calendar tasks and flags hazardous or unsafe suggestions (e.g. burning crops, improper chemical use); results shown in the Pest & Disease Risk assessment.
- **Farming Assistant chat** — Conversational Q&A with context from variable/calendar/persistent; on-demand market and pest data; markdown-rendered responses; government source citations (TNAU, ICAR, Agmarknet).
- **Image disease analysis** — Upload a plant/field image → research agent (GPT + Tavily gov sources) → in-depth disease analysis; optional pass-through to calendar regeneration.

---

## Architecture

| Layer        | Tech                    | Purpose |
|-------------|-------------------------|--------|
| **Backend** | FastAPI (Python)        | Crop calendar API, variable generation, calendar agent, research agent, crop/market/pest agents, chatbot. |
| **Frontend**| React (Vite) + Tailwind | Farmer dashboard, crop setup, calendar, today’s tasks, market prices, pest risk, Ask Assistant (markdown chat). |
| **Optional**| Node.js                 | Auth (MongoDB + JWT), proxy to FastAPI, pest alert emails (nodemailer). |

Data flow: **variable.json** (location, crop, soil, climate) → **persistent.json** (crop timelines from gov sources) → **calendar.json** (day-indexed tasks and weather). All agents read/write these files under `data/`.

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** (for frontend; optional for Node backend)
- **API keys** (see Environment variables)

---

## Environment variables

Create a `.env` file in the project root (`Team_FAB-5_Agritech/`):

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes (for calendar, chat, research, crop extraction, recommender, hazard scan) | OpenAI API key. |
| `TAVILY_API_KEY` | Recommended | Tavily search for research agent, crop agent, market agent (gov/agri sources). |
| `CALENDAR_HAZARD_LLM_MODEL` | No | Model for calendar hazard scan (default: `gpt-4o-mini`). |
| `CALENDAR_OPENAI_MODEL` | No | Calendar generation model (default: `o1-mini`; falls back to `gpt-4o` if unavailable). |
| `NODE_EMAIL_SERVICE_URL` | No | Node email endpoint for pest alerts (default: `http://localhost:3000/api/send-pest-alert`). |

---

## Setup & run

### 1. Backend (FastAPI)

From the project root (`Team_FAB-5_Agritech/`):

```bash
# Create virtual environment (optional but recommended)
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the API
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API base URL: **http://127.0.0.1:8000**  
Docs: **http://127.0.0.1:8000/docs**

### 2. Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Frontend: **http://localhost:5173**

Ensure the frontend is allowed in CORS (default in `main.py`: `http://localhost:5173`, `http://127.0.0.1:5173`).

### 3. Optional: Node backend (auth + email)

For auth and pest alert emails:

```bash
cd nodebackend
cp .env.example .env   # set MONGODB_URI, JWT_SECRET, FASTAPI_URL
npm install
npm run dev
```

Runs on port 3001 by default. Configure frontend to proxy `/api` to this URL if you use auth.

---

## Main API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/generate-variable` | Create/update variable from state, city, crop_name, season. |
| `GET`  | `/variable` | Read current variable. |
| `PATCH`| `/variable` | Update `day_of_cycle` only. |
| `GET`  | `/persistent` | Read persistent crop data. |
| `GET`  | `/calendar` | Read calendar (hazardous tasks filtered out). |
| `POST` | `/generate-calendar` | Generate or remake calendar; optional `disease_analysis` in body. |
| `POST` | `/analyze-image` | Upload image → disease analysis text. |
| `POST` | `/recommend-crops` | City + soil_type → recommended crops + rationale. |
| `POST` | `/predict-market-price` | Crop, state, season, harvest_month → price prediction. |
| `POST` | `/assess-pest-risk` | Pest/disease risk + optional `user_email` for alerts; includes `calendar_hazard_alerts` when LLM finds hazardous calendar tasks. |
| `POST` | `/chat` | Send message, get assistant response (markdown). |
| `GET`  | `/chat/history` | Chat history for session. |
| `DELETE`| `/chat/history` | Clear chat history. |
| `GET`  | `/chat/suggestions` | Quick suggestions. |

---

## Project structure

```
Team_FAB-5_Agritech/
├── main.py                 # FastAPI app and all endpoints
├── requirements.txt        # Python dependencies
├── .env                    # API keys (create from above)
├── data/
│   ├── variable.json      # Location, crop, day_of_cycle, soil, climate
│   ├── persistent.json    # Crop timelines (stages, pesticides, fertilizers)
│   └── calendar.json      # Day-by-day tasks and weather
├── services/
│   ├── generate_variable.py   # Geocode, soil, weather → variable.json
│   ├── calendar_agent.py      # Calendar generation/remake (OpenAI)
│   ├── crop_agent.py          # Tavily gov search + OpenAI → persistent
│   ├── research_agent.py      # Image/text + Tavily + OpenAI → disease analysis
│   └── schemas.py             # Pydantic models
├── agents/
│   ├── chatbot_agent.py       # Farmer Q&A (context + market/pest)
│   ├── market_price_agent.py  # Price prediction + cache
│   ├── pest_disease_agent.py  # Risk assessment + LLM calendar hazard scan
│   └── data/                  # Agent caches (market_prices, pest_disease_risk)
├── crop-prediction/
│   └── crop-prediction-services/  # Weather, rainfall, news, AI recommender
├── frontend/                # React + Vite + Tailwind
└── nodebackend/             # Optional: auth + email
```

---

## Data files

- **variable.json** — Produced by `POST /generate-variable`. Contains location (state, city, coordinates), crop (crop_name, season), day_of_cycle, soil_type, soil_map, soil_properties, climate. Required for calendar and pest risk.
- **persistent.json** — Crop timelines keyed by crop+state (e.g. `rice_maharashtra`). Filled by the crop agent when generating the calendar. Contains seasons, sowing/harvesting months, cycle_duration_days, stages, pesticides, fertilizers.
- **calendar.json** — Produced by `POST /generate-calendar`. Contains weather_baseline, cycle_duration_days, start_day, location, crop, and days[] (day_index, stage_name, tasks, weather). Served with hazardous tasks filtered out; hazard details appear in the pest risk assessment when the LLM flags them.

---

## Safety

- **Calendar tasks** — Responses from `GET /calendar` and `POST /generate-calendar` are sanitized: tasks that match a hazardous blocklist are removed before sending.
- **Calendar hazard assessment** — The pest risk agent runs an LLM over the calendar to flag hazardous or unsafe tasks (e.g. burning crops, unsafe chemical use). Flagged items and reasons are returned in `calendar_hazard_alerts` and shown in the Pest & Disease Risk UI.
- **Pest risk output** — Preventive actions and pest/disease text are sanitized so no hazardous suggestions are returned.

---

## License

See repository or team for license details.
