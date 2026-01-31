"""
OpenAI image + GPT research agent.

Accepts text, image, or both. For image-only (e.g. plant disease), Tavily is
compulsory: identify from image → search government/agri sources → in-depth
analysis and solutions. For text or text+image, optional Tavily via tool-calling.
"""
import base64
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
OPENAI_MODEL = os.getenv("RESEARCH_OPENAI_MODEL", "gpt-4o-mini")
TAVILY_MAX_RESULTS = int(os.getenv("RESEARCH_TAVILY_MAX_RESULTS", "15"))
MAX_TOOL_ROUNDS = int(os.getenv("RESEARCH_MAX_TOOL_ROUNDS", "5"))

# Government/educational domains (irrespective of state) - prefer these in search
GOVERNMENT_DOMAIN_PATTERNS = [
    ".gov.in",
    ".nic.in",
    ".ac.in",
    ".icar.org.in",
    ".gov",
]

# -----------------------------------------------------------------------------
# Tavily: in-depth research, government sites preferred
# -----------------------------------------------------------------------------


def _get_tavily_client() -> TavilyClient:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY not set in .env")
    return TavilyClient(api_key=api_key)


def _is_government_domain(url: str) -> bool:
    try:
        hostname = (urlparse(url).hostname or "").lower()
        return any(hostname.endswith(pat.lower()) for pat in GOVERNMENT_DOMAIN_PATTERNS)
    except Exception:
        return False


def tavily_search_prefer_government(query: str, max_results: int = 15) -> str:
    """
    Search with Tavily; filter to government/educational domains when possible.
    Country=india for .gov.in etc.; also returns .gov (international) if matched.
    """
    client = _get_tavily_client()
    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=max_results * 2,  # fetch more so we have enough after filter
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
        if len(parts) >= max_results:
            break
    if parts:
        return "\n\n---\n\n".join(parts)
    # Fallback: if no government results, return first few results so agent still has context
    parts = []
    for r in response.get("results", [])[:max_results]:
        url = r.get("url", "")
        title = r.get("title", "")
        c = r.get("content", "")
        if c:
            gov_note = " [government/educational]" if _is_government_domain(url) else ""
            parts.append(f"[Source: {title} ({url}){gov_note}]\n{c}")
    return "\n\n---\n\n".join(parts) if parts else "No results found."


# -----------------------------------------------------------------------------
# Image input: path or base64 -> content for OpenAI
# -----------------------------------------------------------------------------


def _mime_from_path(path: str | Path) -> str:
    p = Path(path)
    suf = (p.suffix or "").lower()
    if suf == ".png":
        return "image/png"
    if suf in (".gif", ".webp"):
        return f"image/{suf[1:]}"
    return "image/jpeg"


def _build_image_url(image_path: str | Path | None, image_base64: str | None) -> str | None:
    """Return data URL for OpenAI image_url content, or None if no image. image_path takes precedence if both set."""
    if image_path:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")
        mime = _mime_from_path(path)
        with open(path, "rb") as f:
            b64 = base64.standard_b64encode(f.read()).decode("ascii")
        return f"data:{mime};base64,{b64}"
    if image_base64:
        raw = image_base64.strip()
        if raw.startswith("data:"):
            return raw
        return f"data:image/jpeg;base64,{raw}"
    return None


# -----------------------------------------------------------------------------
# OpenAI tools for agent
# -----------------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "tavily_search",
            "description": (
                "Search the web for in-depth information. Prefer government and educational "
                "sources (.gov.in, .nic.in, .ac.in, .icar.org.in, .gov). Use when you need "
                "current, detailed, or authoritative information to answer the user's query."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find relevant information.",
                    },
                },
                "required": ["query"],
            },
        },
    },
]


# -----------------------------------------------------------------------------
# Image-only disease analysis: compulsory Tavily (identify → search → synthesize)
# -----------------------------------------------------------------------------

DISEASE_QUERY_PROMPT = """Look at this plant/crop image. Identify the disease, pest, or disorder shown.
Reply with ONLY one search query to find authoritative management and treatment information from government or agricultural research sources (e.g. India: gov.in, icar.org.in, TNAU). Do not add any other text—only the search query."""

DISEASE_SYNTHESIS_PROMPT = """Using the image and the search results below, provide an in-depth analysis.

**1. Identification & description**
- Name of the disease/pest/disorder and causal agent if known.
- Clear description of symptoms visible in the image.

**2. Causes & conditions**
- What causes it and under what conditions it spreads.

**3. Evidence-based solutions & management**
- Cultural practices (sanitation, water, nutrition, resistant varieties).
- Chemical control (fungicides/pesticides) with recommended products and doses where available.
- Biological control if relevant.
- Prevention and monitoring.

Use only information from the search results and the image. Prefer government/ICAR/TNAU recommendations. Structure with clear sections and bullet points. Be specific and actionable."""


def _run_image_only_disease_analysis(client: OpenAI, image_url: str) -> str:
    """Image-only flow: get search query from model → run Tavily (compulsory) → synthesize in-depth answer."""
    # Step 1: Get a search query from the model (image only, no tools)
    messages_query = [
        {"role": "system", "content": "You are a plant pathologist. Reply only with a single search query, no other text."},
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": image_url}},
            {"type": "text", "text": DISEASE_QUERY_PROMPT},
        ]},
    ]
    resp1 = client.chat.completions.create(model=OPENAI_MODEL, messages=messages_query, max_tokens=300)
    query_text = (resp1.choices[0].message.content or "").strip()
    # Use first line or first 200 chars as query; fallback if empty
    search_query = query_text.split("\n")[0].strip() if query_text else "plant disease management India site:gov.in OR site:icar.org.in"
    if not search_query:
        search_query = "plant disease management India site:gov.in OR site:icar.org.in"

    # Step 2: Compulsory Tavily search (government preferred)
    search_results = tavily_search_prefer_government(search_query, max_results=TAVILY_MAX_RESULTS)
    # Optional: second search for "management" or "control" if first is thin
    if len(search_results) < 500:
        search_results += "\n\n---\n\n" + tavily_search_prefer_government(
            search_query + " management fungicide pesticide", max_results=10
        )

    # Step 3: Synthesize in-depth analysis (image + search results)
    messages_synth = [
        {"role": "system", "content": "You are an expert agronomist. Give detailed, evidence-based answers using only the provided image and search content. Prefer government and ICAR/TNAU sources."},
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": image_url}},
            {"type": "text", "text": f"Search results (government/agri sources):\n\n{search_results}\n\n{DISEASE_SYNTHESIS_PROMPT}"},
        ]},
    ]
    resp2 = client.chat.completions.create(model=OPENAI_MODEL, messages=messages_synth, max_tokens=4096)
    return (resp2.choices[0].message.content or "").strip() or "No analysis generated."


# -----------------------------------------------------------------------------
# Agent: messages + optional tool calls loop (for text or text+image when Tavily optional)
# -----------------------------------------------------------------------------


def run_research_agent(
    *,
    text: str | None = None,
    image_path: str | Path | None = None,
    image_base64: str | None = None,
    allow_tavily: bool = True,
) -> str:
    """
    Run the OpenAI image + GPT research agent.

    Accepts text, image, or both. If allow_tavily is True, the model can call
    Tavily search (government sites preferred) to gather more information.
    Returns a detailed answer string.

    Args:
        text: User query or description (optional if image provided).
        image_path: Path to image file (optional).
        image_base64: Base64-encoded image (optional). Overridden by image_path if both set.
        allow_tavily: Whether the model can use Tavily search when needed.

    Returns:
        Detailed answer string.

    Raises:
        ValueError: If both text and image are missing, or API keys missing.
    """
    if not text and not image_path and not image_base64:
        raise ValueError("Provide at least one of: text, image_path, or image_base64.")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in .env.")

    client = OpenAI(api_key=api_key)
    image_url = _build_image_url(image_path, image_base64)

    # Image-only: compulsory Tavily flow (identify → search → in-depth disease analysis)
    if image_url and not (text and text.strip()):
        return _run_image_only_disease_analysis(client, image_url)

    # Build user message content (text + optional image)
    content: list[dict[str, Any]] = []
    if text and text.strip():
        content.append({"type": "text", "text": text.strip()})
    if image_url:
        content.append({"type": "image_url", "image_url": {"url": image_url}})
    if not content:
        content.append({"type": "text", "text": "Please describe what you need help with."})

    system_message = {
        "role": "system",
        "content": (
            "You are an expert research assistant. You can see images and read text. "
            "When you need more current or detailed information, use the tavily_search tool; "
            "prefer government and educational sources. Synthesize all information into a clear, "
            "detailed, well-structured answer. If the user asks about agriculture, crops, pests, "
            "or policy, prioritize Indian government and ICAR/TNAU-type sources when available. "
            "Give actionable, in-depth answers; use bullet points or sections when helpful."
        ),
    }

    messages: list[dict[str, Any]] = [
        system_message,
        {"role": "user", "content": content},
    ]

    tools = TOOLS if allow_tavily else None
    tool_rounds = 0

    while True:
        kwargs: dict[str, Any] = {
            "model": OPENAI_MODEL,
            "messages": messages,
            "max_tokens": 4096,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        msg = choice.message

        if not getattr(msg, "tool_calls", None) or tool_rounds >= MAX_TOOL_ROUNDS:
            # Final answer
            text_content = getattr(msg, "content", None) or ""
            return text_content.strip() or "No response generated."

        # Append assistant message with tool_calls
        assistant_msg: dict[str, Any] = {"role": "assistant", "content": msg.content or None}
        assistant_msg["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in msg.tool_calls
        ]
        messages.append(assistant_msg)

        # Run each tool call and append results
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}
            if name == "tavily_search":
                query = args.get("query", "")
                result = tavily_search_prefer_government(query, max_results=TAVILY_MAX_RESULTS)
            else:
                result = f"Unknown tool: {name}"
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

        tool_rounds += 1


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def _is_image_path(p: Path) -> bool:
    return p.suffix.lower() in (".jpg", ".jpeg", ".png", ".gif", ".webp")


if __name__ == "__main__":
    import sys

    # Usage: python -m services.research_agent image.jpg           (image only, Tavily compulsory)
    #        python -m services.research_agent "query"             (text only)
    #        python -m services.research_agent "query" image.jpg   (both)
    args = sys.argv[1:]
    if not args:
        print("Usage: python -m services.research_agent <image_path>", file=sys.stderr)
        print("       python -m services.research_agent \"Your question\" [image_path]", file=sys.stderr)
        print("       Image-only: in-depth disease analysis with compulsory Tavily search.", file=sys.stderr)
        sys.exit(1)

    text = None
    image_path = None

    if len(args) == 1:
        one = Path(args[0]).resolve()
        if one.exists() and _is_image_path(one):
            image_path = one  # image only
        else:
            text = args[0].strip()  # text only
    else:
        text = args[0].strip() if args[0] else None
        image_path = Path(args[1]).resolve()
        if not image_path.exists():
            print(f"Error: Image file not found: {image_path}", file=sys.stderr)
            sys.exit(1)

    if not text and not image_path:
        print("Error: Provide at least a query or an image path.", file=sys.stderr)
        sys.exit(1)

    try:
        out = run_research_agent(text=text or None, image_path=image_path)
        print(out)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
