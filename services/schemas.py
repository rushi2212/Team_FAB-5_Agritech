"""Pydantic models for crop timeline JSON schema (persistent.json).
Stages are crop-specific (e.g. rice: Nursery, Transplanting, Tillering, PI, Harvesting).
Timing uses percentage of crop cycle (0-100) and calendar months."""
from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class Stage(BaseModel):
    """A crop-specific growth stage (e.g. Nursery, Transplanting, Tillering, Harvesting).
    Names and sequence depend entirely on the crop."""
    name: str
    start_pct: float = Field(..., ge=0, le=100, description="% through crop cycle when stage starts")
    end_pct: float = Field(..., ge=0, le=100, description="% through crop cycle when stage ends")
    description: str = ""
    typical_months: list[str] = Field(default_factory=list, description="Calendar months when this typically occurs")


class Pesticide(BaseModel):
    """Suggested pesticide with timing (percentage-based)."""
    name: str
    stage: str = ""
    start_pct: float = Field(0, ge=0, le=100)
    duration_pct: float = Field(0, ge=0, le=100, description="% of cycle the application spans")
    dosage: str = ""
    target_pests: str = ""


class Fertilizer(BaseModel):
    """Suggested fertilizer with timing (percentage-based)."""
    name: str
    stage: str = ""
    start_pct: float = Field(0, ge=0, le=100)
    duration_pct: float = Field(0, ge=0, le=100)
    schedule: str = ""
    dosage: str = ""


class SeasonData(BaseModel):
    """Per-season timeline (Rabi / Kharif / Summer)."""
    name: str = ""  # Optional; often derived from season key (Rabi/Kharif/Summer)
    sowing_months: list[str] = Field(default_factory=list, description="Calendar months for sowing (e.g. June, July)")
    harvesting_months: list[str] = Field(default_factory=list, description="Calendar months for harvesting")
    cycle_duration_days: int = Field(0, ge=0, description="Approx total cycle length in days")
    stages: list[Stage] = Field(default_factory=list)
    pesticides: list[Pesticide] = Field(default_factory=list)
    fertilizers: list[Fertilizer] = Field(default_factory=list)


class CropEntry(BaseModel):
    """Full crop entry for persistent.json."""
    crop_name: str
    state: str = ""  # e.g. Maharashtra, Karnataka - data is state-specific
    source_domains_used: list[str] = Field(default_factory=list)
    seasons: dict[str, SeasonData] = Field(default_factory=dict)
    last_updated: str = Field(default_factory=lambda: date.today().isoformat())


class MarketPricePrediction(BaseModel):
    """Market price prediction for a crop at harvest time based on historical mandi data."""
    crop_name: str
    state: str = ""
    season: str = ""
    harvest_month: str = Field("", description="Expected harvest month (e.g. October, March)")
    predicted_price_range: dict[str, float] = Field(
        default_factory=dict, 
        description="Min and max price in INR/quintal (e.g. {'min': 1800, 'max': 2200})"
    )
    average_price: float = Field(0.0, description="Average predicted price in INR/quintal")
    trend: str = Field("", description="Price trend: 'rising', 'falling', 'stable', or 'volatile'")
    confidence: str = Field("", description="Data confidence: 'high', 'medium', 'low'")
    data_sources: list[str] = Field(default_factory=list, description="Sources scraped for price data")
    last_updated: str = Field(default_factory=lambda: date.today().isoformat())


class PestDiseaseRisk(BaseModel):
    """Pest and disease risk assessment based on crop stage, weather, and environmental conditions."""
    crop_name: str
    crop_stage: str = Field("", description="Current crop growth stage (e.g. Nursery, Vegetative, Flowering)")
    day_of_cycle: int = Field(0, ge=0, description="Current day in crop cycle")
    risk_level: str = Field("", description="Overall risk level: 'low', 'medium', 'high', 'critical'")
    risk_score: float = Field(0.0, ge=0, le=100, description="Numerical risk score (0-100)")
    pest_risks: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of pest risks with name, severity, and description"
    )
    disease_risks: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of disease risks with name, severity, and description"
    )
    preventive_actions: list[str] = Field(
        default_factory=list,
        description="Recommended preventive actions and treatments"
    )
    weather_factors: dict[str, float] = Field(
        default_factory=dict,
        description="Weather conditions influencing risk (temperature, humidity, rainfall)"
    )
    email_sent: bool = Field(False, description="Whether alert email was sent to user")


class ChatMessage(BaseModel):
    """A single message in the chat conversation."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(default_factory=lambda: date.today().isoformat(), description="Message timestamp")
    sources: list[str] = Field(default_factory=list, description="Sources cited in this message")


class ChatRequest(BaseModel):
    """Request to chat endpoint with user message."""
    message: str = Field(..., description="User's question or message to the chatbot")
    session_id: str = Field("default", description="Optional session ID for conversation tracking")


class ChatResponse(BaseModel):
    """Response from chatbot with answer and source citations."""
    response: str = Field(..., description="Chatbot's answer in simple, farmer-friendly language")
    sources: list[str] = Field(default_factory=list, description="Government/official sources cited (e.g., TNAU, ICAR, Agmarknet)")
    tools_used: list[str] = Field(default_factory=list, description="Tools invoked to answer the question")
    context: dict[str, Any] = Field(default_factory=dict, description="Current farm context used for the response")
    suggestions: list[str] = Field(default_factory=list, description="Quick action suggestions for the user")


class ChatHistoryResponse(BaseModel):
    """Response containing chat conversation history."""
    history: list[ChatMessage] = Field(default_factory=list, description="List of messages in chronological order")
    session_id: str = Field("default", description="Session ID for this conversation")
    last_updated: str = Field(default_factory=lambda: date.today().isoformat())
