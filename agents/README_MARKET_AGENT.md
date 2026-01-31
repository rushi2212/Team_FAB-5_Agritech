# Market Price Prediction Agent

## Overview
The Market Price Prediction Agent predicts harvest-time market prices for crops using real-time web scraping of Agmarknet and other government mandi (market) data sources. It analyzes historical price patterns, seasonal trends, and current market conditions to provide price forecasts.

## Features

### 1. **Real-time Data Scraping with Tavily**
- Scrapes Agmarknet and government agriculture portals
- Uses Tavily API for intelligent web search and data extraction
- Falls back to synthetic data if Tavily is unavailable

### 2. **Price Analysis**
- Historical price trend analysis (rising/falling/stable/volatile)
- Confidence scoring based on data consistency
- Seasonal pattern recognition (Kharif/Rabi cycles)

### 3. **Intelligent Caching**
- Caches predictions for 7 days to reduce API calls
- Stores results in `agents/data/market_prices.json`
- Automatic cache invalidation

### 4. **Multi-Source Data**
- Agmarknet (primary)
- State agriculture department portals
- Historical price databases

## Usage

### Standalone Testing
```bash
python agents/market_price_agent.py <crop> <state> <season> <harvest_month>
```

**Example:**
```bash
python agents/market_price_agent.py wheat Punjab Rabi March
python agents/market_price_agent.py rice Maharashtra Kharif October
```

### API Endpoint
```http
POST /predict-market-price
Content-Type: application/json

{
  "crop_name": "wheat",
  "state": "Punjab",
  "season": "Rabi",
  "harvest_month": "March"
}
```

**Response:**
```json
{
  "crop_name": "wheat",
  "state": "Punjab",
  "season": "Rabi",
  "harvest_month": "March",
  "predicted_price_range": {
    "min": 1800,
    "max": 2200
  },
  "average_price": 2000,
  "trend": "stable",
  "confidence": "high",
  "data_sources": ["agmarknet", "historical_pattern_analysis"],
  "last_updated": "2026-02-01"
}
```

## Configuration

### Environment Variables (`.env`)
```env
# Tavily API Key (required for real scraping)
TAVILY_API_KEY=your_tavily_api_key_here
```

Get your free Tavily API key at: https://tavily.com

### Cache Settings
- **Location**: `agents/data/market_prices.json`
- **Validity**: 7 days (configurable via `CACHE_VALIDITY_DAYS`)
- **Format**: JSON with crop+state+season keys

## Supported Crops
- **Cereals**: Rice, Wheat, Maize
- **Cash Crops**: Cotton, Sugarcane, Soybean, Groundnut
- **Pulses**: Chickpea (Chana)
- **Vegetables**: Tomato, Onion, Potato

## Price Trends
- **Rising**: Prices increasing >1.5% per month
- **Falling**: Prices decreasing >1.5% per month
- **Stable**: Price change <1.5% per month
- **Volatile**: High variation (CV >15%)

## Confidence Levels
- **High**: Low volatility (<8%), 18+ months data
- **Medium**: Moderate volatility (<15%), 12+ months data
- **Low**: High volatility or limited data

## Data Flow
1. Check cache for recent prediction (< 7 days old)
2. If cache miss, scrape using Tavily API
3. Extract price data from search results
4. Analyze trends and calculate predictions
5. Cache result for future requests
6. Return prediction with confidence metrics

## Testing
Run the comprehensive test suite:
```bash
python test_market_agent.py
```

## Fallback Behavior
If Tavily is unavailable or no API key is provided:
- Uses synthetic data based on:
  - Base prices for common crops
  - Seasonal patterns (Kharif/Rabi cycles)
  - Historical volatility models

## Integration with Calendar Agent
The market price agent can be integrated with the calendar agent to provide:
- Optimal sowing time recommendations based on expected prices
- Harvest timing optimization for maximum profit
- Risk assessment for volatile markets

## Future Enhancements
- [ ] Add more data sources (NCDEX, commodity exchanges)
- [ ] ML-based price forecasting
- [ ] Regional market variation analysis
- [ ] Export opportunity identification
- [ ] Price alert notifications
