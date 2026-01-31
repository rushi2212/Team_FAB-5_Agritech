"""
Crop timeline agent: checks persistent.json for a crop; if missing, uses Tavily
(government domains only) to scrape crop data, structures it with OpenAI,
and saves to persistent.json. Uses LangChain for tools and extraction.
"""
import json
import os
from datetime import date
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

from dotenv import load_dotenv
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from tavily import TavilyClient

from schemas import CropEntry

load_dotenv()

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
# Data folder at project root; script lives in services/
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PERSISTENT_PATH = _DATA_DIR / "persistent.json"

# Domain patterns to accept (checked via endswith on the hostname)
# Tavily doesn't support wildcards, so we search broadly and filter results.
GOVERNMENT_DOMAIN_PATTERNS = [
    ".gov.in",
    ".nic.in",
    ".ac.in",
    ".icar.org.in",
]

# -----------------------------------------------------------------------------
# Persistent I/O
# -----------------------------------------------------------------------------
def load_persistent() -> dict[str, Any]:
    """Load persistent.json; return {} if missing or empty."""
    if not PERSISTENT_PATH.exists() or PERSISTENT_PATH.stat().st_size == 0:
        return {}
    with open(PERSISTENT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def save_persistent(data: dict[str, Any]) -> None:
    """Write dict to persistent.json."""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(PERSISTENT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def normalize_crop_key(crop_name: str, state: Optional[str] = None) -> str:
    """Normalize crop+state for use as JSON key (e.g. rice_maharashtra)."""
    crop = (crop_name or "").strip().lower().replace(" ", "_")
    if state and state.strip():
        st = state.strip().lower().replace(" ", "_")
        return f"{crop}_{st}"
    return crop


# -----------------------------------------------------------------------------
# Tavily government-only search
# -----------------------------------------------------------------------------
def _get_tavily_client() -> TavilyClient:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY not set in .env")
    return TavilyClient(api_key=api_key)


def _is_government_domain(url: str) -> bool:
    """Check if URL belongs to an Indian government/university domain."""
    try:
        hostname = urlparse(url).hostname or ""
        return any(hostname.endswith(pat) for pat in GOVERNMENT_DOMAIN_PATTERNS)
    except Exception:
        return False


def tavily_search_government(query: str, max_results: int = 20) -> str:
    """
    Search using Tavily with country=india, filter to .gov.in / .nic.in / .ac.in.
    State preference comes from the query (e.g. "rice maharashtra") - no hardcoded domains.
    """
    client = _get_tavily_client()
    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=max_results,
        country="india",
    )
    parts = []
    for r in response.get("results", []):
        url = r.get("url", "")
        if not _is_government_domain(url):
            continue
        title = r.get("title", "")
        content = r.get("content", "")
        if content:
            parts.append(f"[Source: {title} ({url})]\n{content}")
    return "\n\n---\n\n".join(parts) if parts else "No results found from government sources."


# -----------------------------------------------------------------------------
# LLM structured extraction
# -----------------------------------------------------------------------------
def extract_crop_entry(
    crop_name: str, search_content: str, state: Optional[str] = None
) -> CropEntry:
    """
    Use OpenAI to extract a structured CropEntry from raw search content.
    """
    parser = PydanticOutputParser(pydantic_object=CropEntry)
    format_instructions = parser.get_format_instructions()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You extract COMPLETE, DETAILED crop timeline data from Indian government/agriculture "
                "source text (TNAU, ICAR, state agri depts, etc.). Be thorough—extract ALL information available.\n\n"
                "CRITICAL: Stages are CROP-SPECIFIC, not generic. Different crops have different stages:\n"
                "- Rice: Nursery, Main field prep, Transplanting, Vegetative/Tillering, Panicle initiation, "
                "Booting, Flowering, Grain filling, Maturity, Harvesting\n"
                "- Wheat: Sowing, Crown root, Tillering, Jointing, Booting, Flowering, Dough, Maturity, Harvesting\n"
                "- Cotton: Sowing, Squaring, Flowering, Boll formation, Boll opening, Harvesting\n"
                "Look up the ACTUAL growth stages for this crop in the source text—do NOT use predefined lists.\n\n"
                "TIMING: Use percentage (0-100) of total crop cycle, NOT days. Compute percentages from cycle duration.\n"
                "Example: if cycle is 120 days and harvesting is days 110-120, harvesting is 92-100%.\n\n"
                "REQUIRED per season: sowing_months (calendar months, e.g. June July), harvesting_months, "
                "cycle_duration_days, and a COMPLETE list of stages from sowing to harvesting (MUST include harvesting).\n"
                "Extract ALL pesticides and fertilizers mentioned with their stage, timing (as start_pct/duration_pct), dosage.\n"
                "source_domains_used: list domains from the snippets (e.g. agritech.tnau.ac.in). "
                "Include state in crop_entry when the data is state-specific."
            ),
            (
                "human",
                "Crop: {crop_name}\nState: {state}\n\nRaw text from government sources:\n\n{search_content}\n\n"
                "{format_instructions}",
            ),
        ]
    )
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = prompt | llm | parser
    result = chain.invoke(
        {
            "crop_name": crop_name,
            "state": state or "",
            "search_content": search_content[:120000],
            "format_instructions": format_instructions,
        }
    )
    if not isinstance(result, CropEntry):
        result = CropEntry.model_validate(result)
    result.crop_name = crop_name
    if state and state.strip():
        result.state = state.strip()
    result.last_updated = date.today().isoformat()
    return result


# -----------------------------------------------------------------------------
# Tools for agent (LangChain @tool)
# -----------------------------------------------------------------------------
@tool
def read_persistent(crop_name: str, state: Optional[str] = None) -> str:
    """
    Read persistent.json and check if crop+state data exists.
    Input: crop name (e.g. 'rice'), state (e.g. 'maharashtra'). Returns JSON with 'found' and 'data'.
    """
    data = load_persistent()
    key = normalize_crop_key(crop_name, state)
    if key in data:
        return json.dumps({"found": True, "data": data[key]}, indent=2)
    return json.dumps({"found": False, "data": None})


@tool
def tavily_search_government_tool(query: str) -> str:
    """
    Search government/agriculture websites only (Indian gov and agri universities).
    Use for package of practices, sowing, harvesting, Rabi, Kharif, Summer, pesticides, fertilizers.
    Input: search query string.
    """
    return tavily_search_government(query, max_results=15)


@tool
def in_depth_crop_search(
    crop_name: str, state: Optional[str] = None, season: Optional[str] = None
) -> str:
    """
    Run multiple targeted searches for thorough crop data from government sources.
    When state is provided, prefer sources from that state (e.g. Maharashtra).
    """
    return _run_in_depth_searches(crop_name, state, season)


@tool
def save_crop_to_persistent(crop_entry_json: str) -> str:
    """
    Save a single crop entry to persistent.json. Merges with existing data.
    Input: JSON string of the crop entry (must have crop_name, seasons with stages/pesticides/fertilizers, etc.).
    """
    try:
        raw = json.loads(crop_entry_json)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"
    try:
        entry = CropEntry.model_validate(raw)
    except Exception as e:
        return f"Validation error: {e}"
    key = normalize_crop_key(entry.crop_name, entry.state)
    data = load_persistent()
    data[key] = entry.model_dump(mode="json")
    save_persistent(data)
    return json.dumps({"ok": True, "key": key, "message": "Saved to persistent.json"})


@tool
def extract_crop_json(
    crop_name: str, search_content: str, state: Optional[str] = None
) -> str:
    """
    Extract structured crop timeline JSON from raw search content using LLM.
    Input: crop_name, search_content, state (optional, e.g. 'maharashtra').
    """
    entry = extract_crop_entry(crop_name, search_content, state=state)
    return entry.model_dump_json(indent=2)


# -----------------------------------------------------------------------------
# ReAct agent (optional: uses tools; main entrypoint is ensure_crop_data)
# -----------------------------------------------------------------------------
def get_crop_agent_tools() -> list:
    """Tools for the ReAct agent: read persistent, in-depth search, extract JSON, save."""
    return [
        read_persistent,
        in_depth_crop_search,
        tavily_search_government_tool,
        extract_crop_json,
        save_crop_to_persistent,
    ]


def run_crop_agent(
    crop_name: str, state: Optional[str] = None, season: Optional[str] = None
) -> dict[str, Any]:
    """
    Run the ReAct agent to ensure crop+state data: read persistent, search if missing,
    extract structured data, and save. Returns the crop entry from persistent.
    """
    try:
        from langgraph.prebuilt import create_react_agent
    except ImportError:
        raise ImportError("langgraph is required for run_crop_agent; use ensure_crop_data instead.")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = create_react_agent(llm, get_crop_agent_tools())
    state_part = f" in {state}" if state else ""
    query = (
        f"Ensure crop data for '{crop_name}'{state_part} is in persistent. "
        "First call read_persistent with crop_name and state. If found, return that data and stop. "
        "If not found, call in_depth_crop_search with crop_name, state, and season. "
        "Then call extract_crop_json with crop_name, the full search content, and state. "
        "Then call save_crop_to_persistent with the JSON string. Return the final crop entry."
    )
    if season:
        query += f" Focus on season: {season}."
    result = agent.invoke({"messages": [{"role": "user", "content": query}]})
    data = load_persistent()
    key = normalize_crop_key(crop_name, state)
    if key in data:
        return data[key]
    # Fallback: return last assistant message if no save happened
    raise RuntimeError("Agent did not save crop data; check tool results.")


# -----------------------------------------------------------------------------
# Entrypoint: ensure crop data is in persistent (run search + save if missing)
# -----------------------------------------------------------------------------
def _run_in_depth_searches(
    crop_name: str, state: Optional[str], season: Optional[str]
) -> str:
    """Run multiple targeted searches for thorough, in-depth government-sourced data.
    When state is provided, include it in queries and prioritize state government sources."""
    base = f"{crop_name} {state}" if state and state.strip() else crop_name
    queries = [
        f"{base} package of practices complete growth stages TNAU ICAR",
        f"{base} sowing harvesting months Rabi Kharif Summer calendar schedule",
        f"{base} crop duration days stages tillering flowering grain filling",
        f"{base} recommended pesticides insecticides disease management",
        f"{base} fertilizer schedule NPK basal top dressing split application",
    ]
    if season:
        queries.insert(0, f"{base} {season} sowing harvesting months stages")

    all_content: list[str] = []
    seen_blocks: set[str] = set()
    for q in queries:
        content = tavily_search_government(q, max_results=15)
        if "No results found" in content:
            continue
        for block in content.split("\n\n---\n\n"):
            block = block.strip()
            if len(block) > 200 and block[:100] not in seen_blocks:
                seen_blocks.add(block[:100])
                all_content.append(block)
    return "\n\n---\n\n".join(all_content) if all_content else ""


def ensure_crop_data(
    crop_name: str,
    state: Optional[str] = None,
    season: Optional[str] = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """
    If crop+state pair is already in persistent.json, return it (unless force_refresh=True).
    Otherwise, run in-depth government-domain searches (preferring state sources),
    extract structured data with OpenAI, save to persistent.json, and return the new entry.
    """
    data = load_persistent()
    key = normalize_crop_key(crop_name, state)
    if key in data and not force_refresh:
        return data[key]

    search_content = _run_in_depth_searches(crop_name, state, season)
    if not search_content:
        raise RuntimeError(
            "No results from government domains. Try another crop or check TAVILY_API_KEY."
        )

    entry = extract_crop_entry(crop_name, search_content, state=state)
    data = load_persistent()
    data[key] = entry.model_dump(mode="json")
    save_persistent(data)
    return data[key]


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    args = [a for a in sys.argv[1:] if a not in ("--refresh", "-r")]
    force = "--refresh" in sys.argv or "-r" in sys.argv
    crop = (args[0] if args else "rice").strip()
    state = None
    season = None
    if len(args) >= 2:
        if args[1].lower() in ("rabi", "kharif", "summer"):
            season = args[1]
        else:
            state = args[1]
    if len(args) >= 3:
        season = args[2]
    try:
        result = ensure_crop_data(
            crop, state=state, season=season, force_refresh=force
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
