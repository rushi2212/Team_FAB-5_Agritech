"""
FastAPI app for crop calendar pipeline.
Step 1: Generate variable (state, city, crop, season) -> variable.json
Step 2: Read variable, persistent, calendar; generate/remake calendar when needed.
"""
import json
import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import time

# Debug: set DEBUG=0 to disable; default on so uvicorn terminal shows all debugging
DEBUG = os.environ.get("DEBUG", "1") != "0" and (os.environ.get("CROP_DEBUG", "1") != "0")
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("crop-api")
if DEBUG:
    log.setLevel(logging.DEBUG)

# Project root; data and services live here
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
VARIABLE_PATH = DATA_DIR / "variable.json"
PERSISTENT_PATH = DATA_DIR / "persistent.json"
CALENDAR_PATH = DATA_DIR / "calendar.json"

app = FastAPI(
    title="Crop Calendar API",
    description="Step 1: Generate variable (location, crop, soil, climate). Step 2: Get/generate calendar.",
    version="1.0.0",
)

# Allow frontend (Vite dev server) to call Python backend directly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def debug_request_logging(request: Request, call_next):
    """Log every request and response to the uvicorn terminal."""
    start = time.perf_counter()
    method = request.method
    path = request.url.path
    client = request.client.host if request.client else "?"
    log.debug(">>> %s %s (client=%s)", method, path, client)
    if request.query_params:
        log.debug("    query=%s", dict(request.query_params))
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    log.debug("<<< %s %s -> %s (%.1f ms)", method, path, response.status_code, elapsed_ms)
    return response


# ---------------------------------------------------------------------------
# Request/response models
# ---------------------------------------------------------------------------

class GenerateVariableRequest(BaseModel):
    """Step 1: inputs for generating variable.json."""
    state: str = Field(..., min_length=1, description="State (e.g. Maharashtra)")
    city: str = Field(..., min_length=1, description="City (e.g. Pune)")
    crop_name: str = Field(..., min_length=1, description="Crop name (e.g. rice)")
    season: str = Field(..., description="Kharif, Rabi, or Summer")


class UpdateDayOfCycleRequest(BaseModel):
    """Update only day_of_cycle in variable.json."""
    day_of_cycle: int = Field(..., ge=1, description="Current day in the crop cycle (1-based)")


class PredictMarketPriceRequest(BaseModel):
    """Request model for market price prediction."""
    crop_name: str = Field(..., min_length=1, description="Crop name (e.g. rice, wheat)")
    state: str = Field(..., min_length=1, description="State (e.g. Maharashtra)")
    season: str = Field(..., description="Kharif, Rabi, or Summer")
    harvest_month: str = Field(..., description="Expected harvest month (e.g. October, March)")


class AssessPestRiskRequest(BaseModel):
    """Request model for pest/disease risk assessment."""
    user_email: str = Field("", description="Email for alerts (optional, only sent if risk >= medium)")


# ---------------------------------------------------------------------------
# Step 1: Generate variable
# ---------------------------------------------------------------------------

@app.post("/generate-variable", response_class=JSONResponse)
def generate_variable_endpoint(body: GenerateVariableRequest):
    """
    Step 1: Generate variable.json from state, city, crop_name, season.
    Fetches geocoding, soil (SoilGrids), and weather (Open-Meteo); writes data/variable.json.
    """
    log.debug("POST /generate-variable body=%s", body.model_dump())
    try:
        from services.generate_variable import generate_variable as run_generate
        out = run_generate(
            state=body.state,
            city=body.city,
            crop_name=body.crop_name,
            season=body.season,
        )
        log.debug("generate-variable ok -> %s", VARIABLE_PATH)
        return out
    except ValueError as e:
        log.debug("generate-variable ValueError: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        log.debug("generate-variable RuntimeError: %s", e)
        raise HTTPException(status_code=502, detail=str(e))


# ---------------------------------------------------------------------------
# Read data (variable, persistent, calendar)
# ---------------------------------------------------------------------------

def _read_json(path: Path, name: str):
    log.debug("_read_json %s", path)
    if not path.exists():
        log.debug("_read_json 404 %s", name)
        raise HTTPException(status_code=404, detail=f"{name} not found. Run step 1 first.")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        log.debug("_read_json ok %s", name)
        return data
    except (json.JSONDecodeError, OSError) as e:
        log.debug("_read_json error %s: %s", name, e)
        raise HTTPException(status_code=500, detail=f"Invalid {name}: {e}")


@app.get("/variable", response_class=JSONResponse)
def get_variable():
    """Return current variable.json (location, crop, soil, climate)."""
    log.debug("GET /variable")
    return _read_json(VARIABLE_PATH, "variable.json")


@app.patch("/variable", response_class=JSONResponse)
def update_day_of_cycle(body: UpdateDayOfCycleRequest):
    """Update day_of_cycle in variable.json. Use before replan (generate-calendar)."""
    log.debug("PATCH /variable day_of_cycle=%s", body.day_of_cycle)
    if not VARIABLE_PATH.exists():
        log.debug("PATCH /variable 404 variable.json missing")
        raise HTTPException(status_code=404, detail="variable.json not found. Run generate-variable first.")
    try:
        with open(VARIABLE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        log.debug("PATCH /variable read error: %s", e)
        raise HTTPException(status_code=500, detail=f"Invalid variable.json: {e}") from e
    if not isinstance(data, dict):
        raise HTTPException(status_code=500, detail="variable.json must be a JSON object.")
    data["day_of_cycle"] = body.day_of_cycle
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(VARIABLE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log.debug("PATCH /variable ok day_of_cycle=%s", body.day_of_cycle)
    return data


@app.get("/persistent", response_class=JSONResponse)
def get_persistent():
    """Return persistent.json (crop data per state)."""
    return _read_json(PERSISTENT_PATH, "persistent.json")


@app.get("/calendar", response_class=JSONResponse)
def get_calendar():
    """Return calendar.json if present (full or from start_day to end)."""
    log.debug("GET /calendar")
    if not CALENDAR_PATH.exists() or CALENDAR_PATH.stat().st_size == 0:
        log.debug("GET /calendar 404")
        raise HTTPException(status_code=404, detail="Calendar not found. Run generate-calendar first.")
    return _read_json(CALENDAR_PATH, "calendar.json")


# ---------------------------------------------------------------------------
# Step 2: Generate / remake calendar
# ---------------------------------------------------------------------------

@app.post("/generate-calendar", response_class=JSONResponse)
def generate_calendar_endpoint():
    """
    Step 2: Run calendar agent. Uses variable.json and persistent.json.
    Creates or remakes calendar when threshold is hit; returns calendar or message.
    """
    log.debug("POST /generate-calendar")
    try:
        import sys
        from io import StringIO
        from services.calendar_agent import run as run_calendar_agent
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            run_calendar_agent()
            msg = sys.stdout.getvalue().strip()
            log.debug("calendar_agent stdout: %s", msg[:200] if msg else "(none)")
        finally:
            sys.stdout = old_stdout
        if CALENDAR_PATH.exists():
            with open(CALENDAR_PATH, "r", encoding="utf-8") as f:
                out = json.load(f)
            log.debug("POST /generate-calendar ok -> calendar.json")
            return out
        log.debug("POST /generate-calendar ok (no file) message=%s", msg)
        return {"message": msg or "Calendar run completed."}
    except FileNotFoundError as e:
        log.debug("POST /generate-calendar FileNotFoundError: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        log.debug("POST /generate-calendar ValueError: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.debug("POST /generate-calendar Exception: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Market Price Prediction
# ---------------------------------------------------------------------------

@app.post("/predict-market-price", response_class=JSONResponse)
def predict_market_price_endpoint(body: PredictMarketPriceRequest):
    """
    Predict harvest-time market prices for a crop based on historical mandi data,
    seasonality, and current trends. Uses agents/market_price_agent.py.
    """
    log.debug("POST /predict-market-price body=%s", body.model_dump())
    try:
        from agents.market_price_agent import run as run_price_agent
        
        result = run_price_agent(
            crop=body.crop_name,
            state=body.state,
            season=body.season,
            harvest_month=body.harvest_month,
        )
        log.debug("POST /predict-market-price ok -> prediction=%s", result.get("average_price"))
        return result
    except ValueError as e:
        log.debug("POST /predict-market-price ValueError: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.debug("POST /predict-market-price Exception: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Pest & Disease Risk Assessment
# ---------------------------------------------------------------------------

@app.post("/assess-pest-risk", response_class=JSONResponse)
def assess_pest_risk_endpoint(body: AssessPestRiskRequest):
    """
    Assess pest and disease risks for current crop based on weather conditions
    and crop stage. Sends email alert if risk is medium or higher.
    Uses agents/pest_disease_agent.py.
    """
    log.debug("POST /assess-pest-risk body=%s", body.model_dump())
    try:
        from agents.pest_disease_agent import run as run_pest_agent
        
        result = run_pest_agent(user_email=body.user_email)
        log.debug("POST /assess-pest-risk ok -> risk_level=%s", result.get("risk_level"))
        return result
    except FileNotFoundError as e:
        log.debug("POST /assess-pest-risk FileNotFoundError: %s", e)
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        log.debug("POST /assess-pest-risk ValueError: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.debug("POST /assess-pest-risk Exception: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def root():
    """Health and steps overview."""
    log.debug("GET /")
    return {
        "service": "Crop Calendar API",
        "step_1": "POST /generate-variable  (body: state, city, crop_name, season)",
        "step_2": "POST /generate-calendar   (uses variable + persistent)",
        "read": "GET /variable, GET /persistent, GET /calendar",
        "predict": "POST /predict-market-price (body: crop_name, state, season, harvest_month)",
        "assess": "POST /assess-pest-risk (body: user_email - optional)",
        "chat": "POST /chat (body: message, session_id - optional)",
    }


# ---------------------------------------------------------------------------
# Chatbot / Farmer Interaction Agent
# ---------------------------------------------------------------------------

# Global chatbot instances (keyed by session_id)
chatbot_instances = {}

def get_chatbot_instance(session_id: str = "default"):
    """Get or create a chatbot instance for a session."""
    if session_id not in chatbot_instances:
        from agents.chatbot_agent import create_chatbot
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        chatbot_instances[session_id] = create_chatbot(api_key, str(DATA_DIR))
    return chatbot_instances[session_id]


@app.post("/chat", response_model=None)
def chat_endpoint(body: dict):
    """
    Chat with the farmer interaction agent. The agent can:
    - Answer questions about crop cultivation
    - Provide calendar tasks and schedules
    - Predict market prices
    - Assess pest/disease risks
    - Explain weather impacts
    - Give soil-based recommendations
    
    All responses cite government sources (TNAU, ICAR, Agmarknet, etc.)
    """
    from services.schemas import ChatRequest, ChatResponse
    
    log.debug("POST /chat body=%s", body)
    try:
        # Validate request
        request = ChatRequest(**body)
        
        # Get chatbot instance
        chatbot = get_chatbot_instance(request.session_id)
        
        # Process message
        result = chatbot.chat(request.message)
        
        # Get quick suggestions
        suggestions = chatbot.get_quick_suggestions()
        
        # Build response
        response = ChatResponse(
            response=result['response'],
            sources=result.get('sources', []),
            tools_used=result.get('tools_used', []),
            context=result.get('context', {}),
            suggestions=suggestions
        )
        
        log.debug("POST /chat ok -> response length=%d, sources=%d", 
                  len(response.response), len(response.sources))
        return response.model_dump()
        
    except ValueError as e:
        log.debug("POST /chat ValueError: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error("POST /chat Exception: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat/history")
def get_chat_history(session_id: str = "default"):
    """
    Get chat conversation history for a session.
    """
    log.debug("GET /chat/history session_id=%s", session_id)
    try:
        from services.schemas import ChatHistoryResponse, ChatMessage
        
        if session_id not in chatbot_instances:
            return ChatHistoryResponse(history=[], session_id=session_id).model_dump()
        
        chatbot = chatbot_instances[session_id]
        history = chatbot.get_history()
        
        # Convert to ChatMessage objects
        messages = [
            ChatMessage(
                role=msg['role'],
                content=msg['content'],
                timestamp=msg.get('timestamp', ''),
                sources=msg.get('sources', [])
            ) for msg in history
        ]
        
        response = ChatHistoryResponse(history=messages, session_id=session_id)
        log.debug("GET /chat/history ok -> %d messages", len(messages))
        return response.model_dump()
        
    except Exception as e:
        log.error("GET /chat/history Exception: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/chat/history")
def clear_chat_history(session_id: str = "default"):
    """
    Clear chat conversation history for a session.
    """
    log.debug("DELETE /chat/history session_id=%s", session_id)
    try:
        if session_id in chatbot_instances:
            chatbot = chatbot_instances[session_id]
            chatbot.clear_history()
            log.debug("DELETE /chat/history ok -> cleared")
            return {"status": "success", "message": "Chat history cleared"}
        else:
            return {"status": "success", "message": "No history to clear"}
            
    except Exception as e:
        log.error("DELETE /chat/history Exception: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat/suggestions")
def get_chat_suggestions(session_id: str = "default"):
    """
    Get context-aware quick action suggestions for the chatbot.
    """
    log.debug("GET /chat/suggestions session_id=%s", session_id)
    try:
        chatbot = get_chatbot_instance(session_id)
        suggestions = chatbot.get_quick_suggestions()
        log.debug("GET /chat/suggestions ok -> %d suggestions", len(suggestions))
        return {"suggestions": suggestions}
        
    except Exception as e:
        log.error("GET /chat/suggestions Exception: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
