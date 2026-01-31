"""Pydantic models for crop timeline JSON schema (persistent.json).
Stages are crop-specific (e.g. rice: Nursery, Transplanting, Tillering, PI, Harvesting).
Timing uses percentage of crop cycle (0-100) and calendar months."""
from datetime import date

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
