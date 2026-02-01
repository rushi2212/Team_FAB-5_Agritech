# SLIDE 2 — IDEA TITLE & PROPOSED SOLUTION

## Problem Statement

Farmers need **location- and crop-aware planning** that combines soil, climate, and crop stage in one place; **disease insight from field images** tied to government and agricultural research sources; **harvest-time price cues** so they can plan when to sell; and **pest/disease risk alerts** based on current weather and growth stage — all in a single, low-friction flow (one setup, one chat, one calendar).

## What Your System Does

1. **Generates farm context (variable)**  
   From state, city, crop, and season: resolves coordinates (Open-Meteo geocoding), fetches soil type and properties at standard depths (ISRIC SoilGrids — WRB classification, clay/sand/silt, pH, organic carbon, bulk density), and current weather (Open-Meteo — temperature, humidity, precipitation). Writes `data/variable.json` with location, crop, day_of_cycle, soil_type, soil_map, soil_properties by depth, and climate — so every downstream agent has a single source of truth.

2. **Builds and updates a day-by-day crop calendar**  
   Uses variable + persistent crop data (stages, pesticides, fertilizers, sowing/harvesting months, cycle duration) and a 16-day Open-Meteo forecast. Ensures crop+state exists in persistent via the crop agent (Tavily gov-only search + OpenAI extraction). When conditions warrant, calls an OpenAI reasoning model (o1-mini / gpt-4o) to plan tasks per day_index with stage names and weather; supports optional disease_analysis from images so the calendar can emphasize disease-management tasks. Writes `data/calendar.json` with weather_baseline, days[] (day_index, stage_name, tasks, weather per day).

3. **Recommends crops**  
   City + soil type are combined with live weather (Open-Meteo or OpenWeatherMap), rainfall bucket (rainfall_scraper), and crop/region news headlines (Google News RSS). An OpenAI-based recommender returns up to three crops and a rationale, prioritizing location-appropriate and soil-suited crops and accounting for climate signals (e.g. drought/flood from news).

4. **Predicts harvest-time market prices**  
   For crop, state, season, and harvest month: uses Tavily to search Agmarknet and government agriculture portals for mandi price data; extracts price patterns from content; filters by harvest month; computes average, min, max, and trend (linear regression slope + volatility). Caches results by crop+state+season for 7 days for fast repeat queries. Returns predicted_price_range, average_price, trend (rising/falling/stable/volatile), and confidence (high/medium/low).

5. **Assesses pest and disease risk**  
   Reads variable (crop, day_of_cycle, climate) and calendar (current stage by day_of_cycle). Uses a crop-specific database (rice, wheat, cotton, tomato, potato) with pests and diseases, their vulnerable stages, humidity/temp ranges, and rainfall triggers. Scores each pest/disease against current weather and stage; aggregates to an overall risk_level (low/medium/high/critical) and risk_score; attaches preventive actions from an IPM-style list. When risk is medium or higher and the user provides an email, sends an alert via the Node email service.

6. **Chat interface**  
   Single conversational entry point: loads variable and calendar for current day_of_cycle, today’s tasks, and stage. Enriches context by keyword — e.g. “price”/“market” triggers market price prediction; “pest”/“disease” triggers pest risk assessment; “calendar”/“upcoming” adds upcoming tasks. Sends context + last 10 messages to GPT-4o; responses cite government sources (TNAU, ICAR, Agmarknet, SoilGrids, Open-Meteo). Keeps last 20 messages per session and offers context-aware quick suggestions (e.g. “What should I do today?”, “What are the market prices?”, “Is there any pest risk?”).

## What Decision the AI Takes Autonomously

- **Calendar agent:** Decides *when to regenerate* the calendar — when there is no calendar yet, when disease_analysis is provided (to weight disease management), or when current climate for the current day deviates from that day’s weather in the calendar beyond configurable thresholds (temperature, humidity, rainfall), so the plan stays aligned with real conditions.
- **Crop agent:** Decides *when to fetch and store* new crop data — when the crop+state key is missing in persistent, so every calendar request has the right stages, pesticides, and fertilizers from government sources.
- **Market agent:** Decides *when to use cached vs fresh* data — 7-day validity per crop+state+season, so repeated queries are fast while data stays reasonably current.
- **Pest agent:** Decides *risk level* (low/medium/high/critical) from crop stage and weather against the pest/disease database, and *when to send an email alert* (risk ≥ medium and user_email provided), so farmers get timely warnings.
- **Chatbot:** Decides *which context to attach* from the user’s message (market prediction, pest risk, calendar/upcoming tasks, crop info from persistent), so answers are relevant without the user having to call separate APIs.
