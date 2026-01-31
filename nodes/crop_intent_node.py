"""
Node 1: CropIntentNode – validate farmer intent (crop, location, sowing_date) using persistent.json catalog.
"""
from __future__ import annotations

from typing import Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from state import FarmGraphState
from knowledge.loaders import get_crop_catalog


def crop_intent_node(state: FarmGraphState) -> dict[str, Any]:
    """Validate crop and region from persistent.json. No DB write."""
    crop = (state.get("crop") or "").strip().lower()
    location = (state.get("location") or "").strip()
    sowing_date = state.get("sowingDate") or ""

    catalog = get_crop_catalog()
    valid = False
    for entry in catalog:
        if entry.get("id", "").lower() == crop:
            regions = entry.get("suitableRegions", [])
            if not regions or location in regions:
                valid = True
            break

    return {
        "crop": crop or state.get("crop"),
        "location": location or state.get("location"),
        "sowingDate": sowing_date or state.get("sowingDate"),
        "knowledgeSourcesUsed": (state.get("knowledgeSourcesUsed") or []) + ["crop_catalog", "regional_suitability"],
    }
