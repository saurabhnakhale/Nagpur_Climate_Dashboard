# Nagpur Climate Impact Dashboard — Easy Starter

This is the easiest first version: Python + Streamlit + OpenWeather. No React, FastAPI or PostgreSQL is required to get started.

## 1. Install
Install Python 3.11+ from https://www.python.org/downloads/
Open this folder in VS Code, then open Terminal.

### Windows PowerShell
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```
If activation is blocked:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 2. Add API key
Create a file named `.env` in the project root and add:
```env
OPENWEATHER_API_KEY="YOUR_REAL_API_KEY"
```
Never upload `.env` to GitHub.

## 3. Run
```powershell
streamlit run app.py
```
Open the local URL shown in the terminal, usually http://localhost:8501

## Features
- Current weather for Nagpur
- 5-day / 3-hour forecast
- Feels-like temperature and humidity indicators
- Forecast rainfall
- OpenWeather air pollution
- Upload aggregated, de-identified disease surveillance CSV and view trends

## OpenWeather endpoints
- Current weather: `/data/2.5/weather`
- Forecast: `/data/2.5/forecast`
- Air pollution: `/data/2.5/air_pollution`

Check your OpenWeather account for endpoint availability, pricing and rate limits. API results are cached for 10 minutes.

## Easiest deployment
1. Push project to GitHub without `.env`.
2. Create an app at https://share.streamlit.io/
3. Select repository and `app.py`.
4. In App settings → Secrets, add:
   `OPENWEATHER_API_KEY = "YOUR_REAL_API_KEY"`
5. Deploy.

## Limitations
- This first version does not continuously store historical weather in a database.
- OpenWeather AQI is a 1–5 scale, not India's CPCB AQI scale (0–500).
- Feels-like temperature is not an official IMD heatwave classification.
- Forecast rainfall is not observed or ward-level rainfall.
- One coordinate does not represent every municipal zone.
- Disease charts show uploaded surveillance trends; they do not predict outbreaks or establish causation.
- Upload only authorized, aggregated, de-identified health data.

## Upgrade later
After this first dashboard works, add automated data collection and PostgreSQL. Only then consider FastAPI + React + Vercel/Render if you need a custom production frontend.
