from fastapi import FastAPI
from dotenv import load_dotenv
from schemas import FarmerInput
from services.weather import get_weather
from services.rainfall_scraper import scrape_rainfall
from services.news_scraper import scrape_crop_news
from services.ai_recommender import recommend_with_ai

load_dotenv()

app = FastAPI(title="Smart Crop Recommendation API")


@app.post("/recommend-crops")
def recommend(input: FarmerInput):

    weather = get_weather(input.city)
    rainfall = scrape_rainfall(input.city)
    news = scrape_crop_news(input.city)

    ai_result = recommend_with_ai(
        city=input.city,
        soil_type=input.soil_type,
        weather=weather,
        rainfall=rainfall,
        news=news,
    )

    return {
        "city": input.city,
        "soil_type": input.soil_type,
        "weather": weather,
        "rainfall": rainfall,
        "crop_news": news,
        "recommended_crops": ai_result.get("crops", []),
        "recommendation_rationale": ai_result.get("rationale", "")
    }
