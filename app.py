import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import sqlite3
import os
import subprocess

st.set_page_config(
    page_title="台灣氣象預報",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_FILE = 'data.db'

REGION_COORDS = {
    '北部':   (25.05, 121.55),
    '中部':   (24.15, 120.70),
    '南部':   (22.80, 120.30),
    '東北部': (24.75, 121.75),
    '東部':   (23.75, 121.55),
    '東南部': (22.70, 121.10),
}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;0,700;1,300;1,400&family=Raleway:wght@300;400;500;600;700&display=swap');

/* ─── TOKENS ─────────────────────────────────────────────── */
:root {
    --ink:      #06101c;
    --abyss:    #040c16;
    --deep:     #0c1d30;
    --mid:      #142840;
    --steel:    #1c3a56;
    --gold:     #c9a96e;
    --gold-lt:  #e8d5a8;
    --gold-dk:  #8a6e3f;
    --sky:      #7a9ab8;
    --frost:    rgba(255,255,255,0.055);
    --frost2:   rgba(255,255,255,0.09);
    --text:     #d2e0ef;
    --muted:    #6d8fa8;
    --border:   rgba(201,169,110,0.18);
    --border2:  rgba(201,169,110,0.35);
}

/* ─── RESET & BASE ───────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main .block-container {
    background: transparent !important;
}

.stApp {
    font-family: 'Raleway', sans-serif;
    color: var(--text);
    background-color: var(--ink);

    /* Clouds photo + dark overlay layers */
    background-image:
        /* Grain texture */
        url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E"),
        /* Dark vignette */
        radial-gradient(ellipse 100% 80% at 50% 0%, rgba(6,16,28,0.55) 0%, rgba(6,16,28,0.82) 70%, rgba(6,16,28,0.97) 100%),
        /* Gold warmth hint */
        linear-gradient(180deg, rgba(201,169,110,0.04) 0%, transparent 40%),
        /* Clouds photo */
        url("/app/static/clouds.jpg");
    background-size: auto, auto, auto, cover;
    background-position: center, center, center, center top;
    background-repeat: repeat, no-repeat, no-repeat, no-repeat;
    background-attachment: fixed, fixed, fixed, fixed;
    min-height: 100vh;
}

#MainMenu, footer, header { visibility: hidden; }

/* ─── SCROLLBAR ──────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; background: var(--abyss); }
::-webkit-scrollbar-thumb { background: var(--steel); border-radius: 3px; }

/* ─── SIDEBAR ────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, #050e19 0%, #060f1c 100%) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, transparent, var(--gold), transparent);
}

/* Sidebar typography */
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown li,
[data-testid="stSidebar"] .stMarkdown a {
    color: var(--muted) !important;
    font-family: 'Raleway', sans-serif !important;
    font-size: .82rem !important;
    letter-spacing: .02em;
    line-height: 1.8;
}
[data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--gold) !important;
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 1.3rem !important;
    font-weight: 400 !important;
    letter-spacing: .18em !important;
    text-transform: uppercase !important;
    margin-bottom: .4rem !important;
}
[data-testid="stSidebar"] .stMarkdown h4 {
    color: var(--sky) !important;
    font-family: 'Raleway', sans-serif !important;
    font-size: .68rem !important;
    font-weight: 700 !important;
    letter-spacing: .2em !important;
    text-transform: uppercase !important;
}
[data-testid="stSidebar"] hr {
    border-color: var(--border) !important;
    margin: 1rem 0 !important;
}

/* Sidebar button */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: 1px solid var(--gold) !important;
    border-radius: 4px !important;
    color: var(--gold) !important;
    font-family: 'Raleway', sans-serif !important;
    font-weight: 600 !important;
    font-size: .78rem !important;
    letter-spacing: .14em !important;
    text-transform: uppercase !important;
    padding: .65rem 1.2rem !important;
    width: 100% !important;
    transition: all .3s ease !important;
    position: relative !important;
    overflow: hidden !important;
}
[data-testid="stSidebar"] .stButton > button::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, var(--gold), var(--gold-dk));
    opacity: 0;
    transition: opacity .3s ease;
}
[data-testid="stSidebar"] .stButton > button:hover {
    color: var(--ink) !important;
}
[data-testid="stSidebar"] .stButton > button:hover::before { opacity: 1; }
[data-testid="stSidebar"] .stButton > button * {
    color: inherit !important;
    position: relative;
    z-index: 1;
}

/* ─── HERO ───────────────────────────────────────────────── */
.hero {
    padding: 3.5rem 2.5rem 3rem;
    margin-bottom: 2.5rem;
    position: relative;
    border-bottom: 1px solid var(--border);
}
.hero::after {
    content: '';
    position: absolute;
    bottom: -1px; left: 0;
    width: 12rem;
    height: 1px;
    background: var(--gold);
}
.hero-overline {
    font-family: 'Raleway', sans-serif;
    font-size: .67rem;
    font-weight: 700;
    letter-spacing: .32em;
    text-transform: uppercase;
    color: var(--gold);
    display: flex;
    align-items: center;
    gap: .8rem;
    margin-bottom: 1.2rem;
}
.hero-overline::before {
    content: '';
    display: inline-block;
    width: 2rem;
    height: 1px;
    background: var(--gold);
}
.hero h1 {
    font-family: 'Cormorant Garamond', serif;
    font-size: 4.2rem;
    font-weight: 300;
    line-height: 1.05;
    color: var(--text);
    margin: 0 0 .8rem;
    letter-spacing: -.02em;
}
.hero h1 em {
    font-style: italic;
    color: var(--gold);
    font-weight: 400;
}
.hero-sub {
    font-size: .8rem;
    color: var(--muted);
    letter-spacing: .08em;
    font-weight: 400;
    display: flex;
    align-items: center;
    gap: 1.2rem;
}
.hero-sub span {
    display: flex;
    align-items: center;
    gap: .4rem;
}
.hero-sub span::before {
    content: '·';
    color: var(--gold);
    font-size: 1.2rem;
    line-height: 1;
}
.hero-sub span:first-child::before { display: none; }

/* ─── SECTION DIVIDER ────────────────────────────────────── */
.sec-head {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin: 2.5rem 0 1.4rem;
}
.sec-head .sec-label {
    font-family: 'Raleway', sans-serif;
    font-size: .65rem;
    font-weight: 700;
    letter-spacing: .28em;
    text-transform: uppercase;
    color: var(--gold);
    white-space: nowrap;
    display: flex;
    align-items: center;
    gap: .6rem;
}
.sec-head .sec-label::before,
.sec-head .sec-label::after {
    content: '◆';
    font-size: .35rem;
    color: var(--gold);
    opacity: .6;
}
.sec-head .sec-line {
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(201,169,110,.3) 0%, transparent 100%);
}

/* ─── CARDS ──────────────────────────────────────────────── */
@keyframes cardIn {
    from { opacity: 0; transform: translateY(18px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes shimmer {
    0%   { left: -120%; }
    100% { left: 120%; }
}

.weather-card {
    background: var(--frost);
    backdrop-filter: blur(16px) saturate(120%);
    -webkit-backdrop-filter: blur(16px) saturate(120%);
    border: 1px solid var(--border);
    border-top: 2px solid rgba(201,169,110,0.25);
    border-radius: 10px;
    padding: 1.4rem .9rem 1.2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    animation: cardIn .55s ease both;
    transition: border-color .3s, background .3s, transform .3s;
}
.weather-card::after {
    content: '';
    position: absolute;
    top: 0; left: -120%;
    width: 60%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.04), transparent);
    transform: skewX(-12deg);
    transition: none;
}
.weather-card:hover {
    border-color: var(--border2);
    border-top-color: var(--gold);
    background: var(--frost2);
    transform: translateY(-4px);
}
.weather-card:hover::after {
    animation: shimmer .65s ease forwards;
}

/* Card stagger */
.weather-card:nth-child(1) { animation-delay: .05s; }
.weather-card:nth-child(2) { animation-delay: .12s; }
.weather-card:nth-child(3) { animation-delay: .19s; }
.weather-card:nth-child(4) { animation-delay: .26s; }
.weather-card:nth-child(5) { animation-delay: .33s; }
.weather-card:nth-child(6) { animation-delay: .40s; }
.weather-card:nth-child(7) { animation-delay: .47s; }

.card-date {
    font-family: 'Raleway', sans-serif;
    font-size: .62rem;
    font-weight: 700;
    letter-spacing: .18em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: .55rem;
}
.card-emoji {
    font-size: 1.9rem;
    line-height: 1.2;
    margin-bottom: .4rem;
}
.card-wx {
    font-size: .67rem;
    font-family: 'Raleway', sans-serif;
    color: var(--muted);
    min-height: 2.6em;
    line-height: 1.5;
    margin-bottom: .6rem;
    padding: 0 .2rem;
}
.card-divider {
    width: 1.5rem;
    height: 1px;
    background: var(--gold);
    opacity: .35;
    margin: 0 auto .6rem;
}
.card-tmax {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.8rem;
    font-weight: 600;
    color: var(--gold);
    line-height: 1;
    letter-spacing: -.01em;
}
.card-tmax sup {
    font-size: .8rem;
    font-weight: 300;
    vertical-align: super;
    color: var(--gold-dk);
    margin-left: 1px;
}
.card-tmin {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.1rem;
    font-weight: 300;
    color: var(--sky);
    margin-top: .1rem;
    letter-spacing: .01em;
}

/* ─── SELECTBOX trigger ──────────────────────────────────── */
[data-testid="stSelectbox"] label { display: none; }
[data-testid="stSelectbox"] > div > div {
    background: rgba(10,22,38,0.9) !important;
    border: 1px solid rgba(201,169,110,0.18) !important;
    border-radius: 6px !important;
    color: #d2e0ef !important;
    font-family: 'Raleway', sans-serif !important;
    font-size: .88rem !important;
    letter-spacing: .05em !important;
}

/* ─── ALERTS ─────────────────────────────────────────────── */
[data-testid="stAlert"] {
    background: rgba(20,40,64,0.5) !important;
    border: 1px solid var(--border) !important;
    border-left: 3px solid var(--gold) !important;
    border-radius: 6px !important;
    color: var(--text) !important;
    font-family: 'Raleway', sans-serif !important;
}

/* ─── CUSTOM TABLE ───────────────────────────────────────── */
.wx-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Raleway', sans-serif;
    font-size: .84rem;
    background: rgba(12,29,48,0.55);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
}
.wx-table thead tr {
    border-bottom: 1px solid rgba(201,169,110,.3);
}
.wx-table th {
    padding: .85rem 1.1rem;
    text-align: left;
    font-size: .63rem;
    font-weight: 700;
    letter-spacing: .18em;
    text-transform: uppercase;
    color: var(--gold);
    background: rgba(201,169,110,.05);
    white-space: nowrap;
}
.wx-table td {
    padding: .8rem 1.1rem;
    color: var(--text);
    border-bottom: 1px solid rgba(255,255,255,0.04);
    vertical-align: middle;
}
.wx-table tbody tr:last-child td { border-bottom: none; }
.wx-table tbody tr:hover td { background: rgba(201,169,110,.04); }
.wx-table .td-date  { color: var(--muted); font-size:.8rem; letter-spacing:.04em; }
.wx-table .td-maxt  { font-family: 'Cormorant Garamond', serif; font-size: 1.1rem; font-weight:600; color: var(--gold); }
.wx-table .td-mint  { font-family: 'Cormorant Garamond', serif; font-size: 1rem;   color: var(--sky); }
.wx-table .td-wx    { color: var(--muted); font-size: .82rem; }

/* ─── MAP CONTAINER ──────────────────────────────────────── */
.element-container iframe {
    border-radius: 10px;
    border: 1px solid var(--border) !important;
}

/* ─── NOTIFICATIONS ──────────────────────────────────────── */
/* Success → gold/amber theme */
[data-testid="stSuccess"],
div[data-testid="stAlert"][data-baseweb="notification"] {
    background: rgba(12,29,48,0.75) !important;
    border: 1px solid rgba(201,169,110,.35) !important;
    border-left: 3px solid var(--gold) !important;
    border-radius: 6px !important;
    color: var(--gold-lt) !important;
    font-family: 'Raleway', sans-serif !important;
}
[data-testid="stSuccess"] svg,
[data-testid="stSuccess"] [data-testid="stMarkdownContainer"] p {
    color: var(--gold-lt) !important;
    fill: var(--gold) !important;
}
/* Error → dark rose */
[data-testid="stError"] {
    background: rgba(30,8,12,.7) !important;
    border: 1px solid rgba(180,80,80,.3) !important;
    border-left: 3px solid rgba(180,80,80,.7) !important;
    border-radius: 6px !important;
    color: #d4a0a0 !important;
    font-family: 'Raleway', sans-serif !important;
}
[data-testid="stError"] svg { fill: #d4a0a0 !important; }
</style>
""", unsafe_allow_html=True)


# ── Utilities ─────────────────────────────────────────────────────────────────
def weather_emoji(wx: str) -> str:
    if not wx:        return "🌤️"
    if "雷" in wx:   return "⛈️"
    if "雨" in wx:   return "🌧️"
    if "雪" in wx:   return "❄️"
    if "陰" in wx:   return "☁️"
    if "多雲" in wx: return "⛅"
    if "晴" in wx:   return "☀️"
    return "🌤️"


def match_coord(region_name: str):
    for key, coord in REGION_COORDS.items():
        if key in region_name:
            return coord
    return None


# ── Data layer ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def load_regions():
    if not os.path.exists(DB_FILE):
        return []
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute('SELECT DISTINCT regionName FROM TemperatureForecasts').fetchall()
    conn.close()
    return [r[0] for r in rows]


@st.cache_data(ttl=600)
def load_region_data(region: str) -> pd.DataFrame:
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(
        'SELECT dataDate, MaxT, MinT, weather FROM TemperatureForecasts '
        'WHERE regionName=? ORDER BY dataDate',
        conn, params=(region,)
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def load_today_all_regions() -> pd.DataFrame:
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query('''
        SELECT t.regionName, t.dataDate, t.MaxT, t.MinT, t.weather
        FROM TemperatureForecasts t
        INNER JOIN (
            SELECT regionName, MIN(dataDate) AS minDate
            FROM TemperatureForecasts GROUP BY regionName
        ) m ON t.regionName = m.regionName AND t.dataDate = m.minDate
    ''', conn)
    conn.close()
    return df


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Weather System")
    st.markdown("---")

    if st.button("↻  更新氣象資料"):
        with st.spinner("正在從中央氣象署抓取最新資料…"):
            result = subprocess.run(['python', 'weather_crawler.py'], capture_output=True, text=True)
            if result.returncode == 0:
                st.cache_data.clear()
                st.markdown("""
                <div style="
                    background:rgba(12,29,48,0.8);
                    border:1px solid rgba(201,169,110,.35);
                    border-left:3px solid #c9a96e;
                    border-radius:6px;
                    padding:.6rem .9rem;
                    font-family:'Raleway',sans-serif;
                    font-size:.82rem;
                    color:#e8d5a8;
                    letter-spacing:.03em;
                ">✦ 資料更新成功</div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="
                    background:rgba(30,8,12,.75);
                    border:1px solid rgba(180,80,80,.3);
                    border-left:3px solid rgba(180,80,80,.7);
                    border-radius:6px;
                    padding:.6rem .9rem;
                    font-family:'Raleway',sans-serif;
                    font-size:.82rem;
                    color:#d4a0a0;
                    letter-spacing:.03em;
                ">✕ 更新失敗</div>
                """, unsafe_allow_html=True)
                st.code(result.stderr)

    st.markdown("---")
    st.markdown("#### 關於")
    st.markdown("""
- 資料來源：**中央氣象署**
- API：`F-A0010-001`
- 儲存：`data.db` (SQLite3)
- 框架：Streamlit + Folium
""")


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-overline">Central Weather Administration · Taiwan</div>
    <h1>台灣<em>氣象</em>預報</h1>
    <div class="hero-sub">
        <span>全台六大分區</span>
        <span>一週天氣預報</span>
        <span>即時資料更新</span>
    </div>
</div>
""", unsafe_allow_html=True)

if not os.path.exists(DB_FILE):
    st.warning("⚠️ 目前無氣象資料，請點擊左側「更新氣象資料」以抓取最新預報。")
    st.stop()

regions = load_regions()
if not regions:
    st.warning("⚠️ 資料庫中無資料，請點擊左側「更新氣象資料」。")
    st.stop()


# ── Map section ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="sec-head">
    <div class="sec-label">全台分區即時概況</div>
    <div class="sec-line"></div>
</div>
""", unsafe_allow_html=True)

today_df = load_today_all_regions()

m = folium.Map(
    location=[23.7, 121.0],
    zoom_start=7,
    tiles='CartoDB dark_matter',
)

for _, row in today_df.iterrows():
    coord = match_coord(row['regionName'])
    if coord is None:
        continue

    emoji = weather_emoji(row['weather'])

    icon_html = f"""
    <div style="
        background: linear-gradient(145deg, #142840, #0c1d30);
        border: 1.5px solid #c9a96e;
        border-radius: 50%;
        width: 64px; height: 64px;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        font-family: 'Raleway', sans-serif;
        box-shadow: 0 0 0 4px rgba(201,169,110,0.12), 0 6px 20px rgba(0,0,0,0.6);
        cursor: pointer;
    ">
        <div style="font-size:1.3rem; line-height:1.1;">{emoji}</div>
        <div style="font-size:.58rem; color:#c9a96e; font-weight:700; letter-spacing:.03em; line-height:1.3;">{row['MaxT']}°<span style="color:#6d8fa8">/{row['MinT']}°</span></div>
    </div>
    """

    popup_html = f"""
    <div style="
        font-family: 'Raleway', sans-serif;
        background: #0c1d30;
        border: 1px solid rgba(201,169,110,.35);
        border-radius: 8px;
        padding: 12px 14px;
        min-width: 160px;
        box-shadow: 0 8px 24px rgba(0,0,0,.5);
    ">
        <div style="font-size:.65rem; letter-spacing:.2em; text-transform:uppercase; color:#c9a96e; margin-bottom:6px; font-weight:700;">{row['regionName']}</div>
        <div style="font-size:.72rem; color:#6d8fa8; margin-bottom:4px;">{row['dataDate']}</div>
        <div style="font-size:.78rem; color:#d2e0ef;">{emoji} {row['weather']}</div>
        <div style="margin-top:8px; display:flex; gap:10px; align-items:baseline;">
            <span style="font-family:'Cormorant Garamond',serif; font-size:1.4rem; color:#c9a96e; font-weight:600; line-height:1;">{row['MaxT']}°</span>
            <span style="font-family:'Cormorant Garamond',serif; font-size:.95rem; color:#6d8fa8;">{row['MinT']}°</span>
        </div>
    </div>
    """

    folium.Marker(
        location=coord,
        icon=folium.DivIcon(html=icon_html, icon_size=(64, 64), icon_anchor=(32, 32)),
        popup=folium.Popup(popup_html, max_width=230),
        tooltip=row['regionName'],
    ).add_to(m)

st_folium(m, height=460, use_container_width=True, returned_objects=[])


# ── Region detail section ─────────────────────────────────────────────────────
st.markdown("""
<div class="sec-head">
    <div class="sec-label">地區詳細預報</div>
    <div class="sec-line"></div>
</div>
""", unsafe_allow_html=True)

selected = st.selectbox("選擇地區", options=regions, label_visibility="collapsed")

if selected:
    df = load_region_data(selected)

    # Daily cards
    cols = st.columns(len(df))
    for idx, row in enumerate(df.itertuples()):
        with cols[idx]:
            date_str = row.dataDate[-5:].replace('-', '/')
            st.markdown(f"""
            <div class="weather-card" style="animation-delay:{idx * 0.07:.2f}s">
                <div class="card-date">{date_str}</div>
                <div class="card-emoji">{weather_emoji(row.weather)}</div>
                <div class="card-wx">{row.weather}</div>
                <div class="card-divider"></div>
                <div class="card-tmax">{row.MaxT}<sup>°C</sup></div>
                <div class="card-tmin">{row.MinT}°</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Chart section
    st.markdown("""
    <div class="sec-head">
        <div class="sec-label">氣溫趨勢</div>
        <div class="sec-line"></div>
    </div>
    """, unsafe_allow_html=True)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['dataDate'], y=df['MaxT'],
        mode='lines+markers+text',
        name='最高氣溫',
        line=dict(color='#c9a96e', width=2.5, shape='spline'),
        marker=dict(size=9, color='#c9a96e', line=dict(width=2, color='#06101c')),
        text=[f"{t}°" for t in df['MaxT']],
        textposition='top center',
        textfont=dict(size=12, color='#e8d5a8', family='Cormorant Garamond'),
        fill='tonexty',
        fillcolor='rgba(201,169,110,0.06)',
    ))
    fig.add_trace(go.Scatter(
        x=df['dataDate'], y=df['MinT'],
        mode='lines+markers+text',
        name='最低氣溫',
        line=dict(color='#7a9ab8', width=2.5, shape='spline'),
        marker=dict(size=9, color='#7a9ab8', line=dict(width=2, color='#06101c')),
        text=[f"{t}°" for t in df['MinT']],
        textposition='bottom center',
        textfont=dict(size=12, color='#6d8fa8', family='Cormorant Garamond'),
        fill='tozeroy',
        fillcolor='rgba(122,154,184,0.04)',
    ))

    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=24, b=20),
        plot_bgcolor='rgba(12,29,48,0.55)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode='x unified',
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
            font=dict(color='#6d8fa8', family='Raleway', size=11),
            bgcolor='rgba(0,0,0,0)',
        ),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=11, color='#6d8fa8', family='Raleway'),
            linecolor='rgba(201,169,110,0.15)',
        ),
        yaxis=dict(
            title='°C',
            gridcolor='rgba(201,169,110,0.06)',
            gridwidth=1,
            zeroline=False,
            tickfont=dict(size=11, color='#6d8fa8', family='Raleway'),
            title_font=dict(color='#6d8fa8', family='Raleway', size=11),
        ),
        hoverlabel=dict(
            bgcolor='#0c1d30',
            bordercolor='#c9a96e',
            font=dict(color='#d2e0ef', family='Raleway', size=12),
        ),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Table section
    st.markdown("""
    <div class="sec-head">
        <div class="sec-label">詳細資料</div>
        <div class="sec-line"></div>
    </div>
    """, unsafe_allow_html=True)

    rows_html = ""
    for row in df.itertuples():
        emoji = weather_emoji(row.weather)
        rows_html += f"""
        <tr>
            <td class="td-date">{row.dataDate}</td>
            <td class="td-maxt">{row.MaxT}°</td>
            <td class="td-mint">{row.MinT}°</td>
            <td class="td-wx">{emoji}&nbsp;{row.weather}</td>
        </tr>"""

    st.markdown(f"""
    <table class="wx-table">
        <thead><tr>
            <th>日期</th>
            <th>最高氣溫</th>
            <th>最低氣溫</th>
            <th>天氣概況</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)

# ── Portal CSS injection (targets Base Web dropdown layer outside React root) ─
components.html("""
<script>
(function injectDropdownStyles() {
    const ID = 'wx-portal-styles';
    if (parent.document.getElementById(ID)) return;
    const style = parent.document.createElement('style');
    style.id = ID;
    style.textContent = `
        @import url('https://fonts.googleapis.com/css2?family=Raleway:wght@400;600&display=swap');

        /* Popup wrapper */
        [data-baseweb="popover"] > div,
        [data-baseweb="select"] [data-baseweb="popover"] > div {
            background: #0b1c2e !important;
            border: 1px solid rgba(201,169,110,0.28) !important;
            border-radius: 8px !important;
            box-shadow: 0 20px 60px rgba(0,0,0,0.75), 0 0 0 1px rgba(201,169,110,0.08) !important;
            overflow: hidden !important;
        }

        /* List container */
        [data-baseweb="menu"],
        [data-baseweb="menu"] ul {
            background: #0b1c2e !important;
            padding: 4px 0 !important;
        }

        /* Each option */
        [data-baseweb="menu"] li {
            background: transparent !important;
            color: #6d8fa8 !important;
            font-family: 'Raleway', sans-serif !important;
            font-size: 0.86rem !important;
            letter-spacing: 0.04em !important;
            padding: 10px 18px !important;
            border-bottom: 1px solid rgba(255,255,255,0.04) !important;
            cursor: pointer !important;
            transition: background 0.15s, color 0.15s !important;
        }
        [data-baseweb="menu"] li:last-child {
            border-bottom: none !important;
        }
        [data-baseweb="menu"] li:hover {
            background: rgba(201,169,110,0.1) !important;
            color: #e8d5a8 !important;
        }
        [data-baseweb="menu"] li[aria-selected="true"] {
            background: rgba(201,169,110,0.14) !important;
            color: #c9a96e !important;
            font-weight: 600 !important;
        }
    `;
    parent.document.head.appendChild(style);
})();
</script>
""", height=0)
