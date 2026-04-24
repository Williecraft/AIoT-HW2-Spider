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

Run the crawler standalone to refresh local weather data:
```bash
python weather_crawler.py
```

## Architecture

Primary app pipeline:

**`weather_crawler.py`** — Fetches JSON from CWA API endpoint `F-A0010-001`, parses the nested structure under `cwaopendata.resources.resource.data.agrWeatherForecasts.weatherForecasts.location`, and writes the normalized result into `data/data.db`. It also exports `data/weather_data.csv` as a secondary inspection file.

**`app.py`** — Streamlit UI that reads from SQLite (`data/data.db`) with cached query helpers. The sidebar "更新氣象資料" button triggers `weather_crawler.py` as a subprocess. The main view includes a Taiwan regional weather map, 7-day forecast cards, a Plotly temperature chart, and a detailed HTML table.

**Data flow:** API → `weather_crawler.py` → `data/data.db` → `app.py` → browser

Generated runtime data in `data/` is gitignored and must be created locally before the app can display weather content.
