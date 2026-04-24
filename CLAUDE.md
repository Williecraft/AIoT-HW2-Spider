# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Taiwan weather forecast system that crawls data from the CWA (Central Weather Administration) Open Data API and displays it via a Streamlit web interface.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```env
CWA_API_TOKEN=your_cwa_api_token
```

Get a token from [CWA Open Data Platform](https://opendata.cwa.gov.tw/).

## Commands

Run the web app (recommended entry point):
```bash
streamlit run app.py
```

Run the crawler standalone to regenerate `weather_data.csv`:
```bash
python weather_crawler.py
```

## Architecture

Two-file pipeline:

**`weather_crawler.py`** — Fetches JSON from CWA API endpoint `F-A0010-001`, parses the nested structure under `cwaopendata.resources.resource.data.agrWeatherForecasts.weatherForecasts.location`, and writes `weather_data.csv` with columns: `Location`, `Date`, `Weather`, `Max_Temperature`, `Min_Temperature`. Uses `ssl.CERT_NONE` to bypass certificate verification.

**`app.py`** — Streamlit UI that reads `weather_data.csv` (cached 10 min via `@st.cache_data`). The sidebar "更新氣象資料" button triggers `weather_crawler.py` as a subprocess. Main view shows per-location 7-day cards using `st.metric`, with an expandable raw dataframe below.

**Data flow:** API → `weather_crawler.py` → `weather_data.csv` → `app.py` → browser

`weather_data.csv` is gitignored and must be generated locally before the app can display data.
