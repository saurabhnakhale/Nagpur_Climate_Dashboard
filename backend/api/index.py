import os
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

LAT, LON = 21.1458, 79.0882
BASE = "https://api.openweathermap.org/data/2.5"

app = FastAPI(title="Nagpur Climate API", version="2.0.0")

origins = [x.strip() for x in os.getenv("FRONTEND_ORIGIN", "*").split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


async def openweather(endpoint: str) -> dict[str, Any]:
    key = os.getenv("OPENWEATHER_API_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="Missing OPENWEATHER_API_KEY environment variable")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"{BASE}/{endpoint}",
                params={"lat": LAT, "lon": LON, "appid": key, "units": "metric"},
            )
        if response.status_code == 401:
            raise HTTPException(status_code=502, detail="OpenWeather rejected the API key. Check key validity.")
        if response.status_code == 429:
            raise HTTPException(status_code=503, detail="OpenWeather rate limit reached.")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"OpenWeather upstream error: {exc.response.status_code}")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Could not connect to OpenWeather")


@app.get("/")
async def root():
    return {"message": "Nagpur Climate API v2.0 is running", "docs": "/docs"}


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "nagpur-climate-api",
        "version": "2.0.0",
        "coordinate": {"lat": LAT, "lon": LON},
    }


@app.get("/api/dashboard")
async def dashboard():
    weather_data  = await openweather("weather")
    forecast_data = await openweather("forecast")

    # Air quality (optional — do not fail if unavailable)
    air = None
    try:
        air_data = await openweather("air_pollution")
        item = air_data.get("list", [{}])[0]
        aqi  = item.get("main", {}).get("aqi")
        air  = {
            "aqi": aqi,
            "category": {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}.get(aqi, "Unavailable"),
            "components": item.get("components", {}),
        }
    except HTTPException:
        pass

    # Current weather
    main     = weather_data.get("main", {})
    wind     = weather_data.get("wind", {})
    wind_ms  = wind.get("speed", 0)
    gust_ms  = wind.get("gust", wind_ms)
    weather = {
        "location":          "Nagpur, Maharashtra",
        "description":       weather_data.get("weather", [{}])[0].get("description", "Unavailable").title(),
        "icon":              weather_data.get("weather", [{}])[0].get("icon", "01d"),
        "observed_at":       datetime.fromtimestamp(
                               weather_data.get("dt", datetime.now(timezone.utc).timestamp()),
                               timezone.utc
                             ).isoformat(),
        "temperature_c":    main.get("temp", 0),
        "feels_like_c":     main.get("feels_like", 0),
        "temp_min_c":       main.get("temp_min", 0),
        "temp_max_c":       main.get("temp_max", 0),
        "humidity_pct":     main.get("humidity", 0),
        "pressure_hpa":     main.get("pressure", 0),
        "wind_kmh":         wind_ms * 3.6,
        "wind_gust_kmh":    gust_ms * 3.6,
        "wind_deg":         wind.get("deg", 0),
        "visibility_km":    weather_data.get("visibility", 0) / 1000,
        "clouds_pct":       weather_data.get("clouds", {}).get("all", 0),
        "rain_last_hour_mm":weather_data.get("rain", {}).get("1h", 0) or 0,
    }

    # Forecast
    forecast = []
    for item in forecast_data.get("list", []):
        fw  = item.get("wind", {})
        fms = fw.get("speed", 0)
        forecast.append({
            "datetime":       datetime.fromtimestamp(item["dt"], timezone.utc).isoformat(),
            "temperature_c":  item.get("main", {}).get("temp", 0),
            "feels_like_c":   item.get("main", {}).get("feels_like", 0),
            "humidity_pct":   item.get("main", {}).get("humidity", 0),
            "pressure_hpa":   item.get("main", {}).get("pressure", 0),
            "rainfall_3h_mm": item.get("rain", {}).get("3h", 0) or 0,
            "wind_kmh":       fms * 3.6,
            "wind_gust_kmh":  fw.get("gust", fms) * 3.6,
            "clouds_pct":     item.get("clouds", {}).get("all", 0),
            "condition":      item.get("weather", [{}])[0].get("description", "").title(),
            "icon":           item.get("weather", [{}])[0].get("icon", "01d"),
        })

    return {"weather": weather, "forecast": forecast, "air": air}
