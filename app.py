import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import sqlite3
import os
import subprocess

# ─── 頁面設定 ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="台灣一週氣象預報",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_FILE = 'data.db'

# 六大分區的地圖中心座標（中央氣象署「農業氣象預報」分區）
REGION_COORDS = {
    '北部':   (25.05, 121.55),
    '中部':   (24.15, 120.70),
    '南部':   (22.80, 120.30),
    '東北部': (24.75, 121.75),
    '東部':   (23.75, 121.55),
    '東南部': (22.70, 121.10),
}

# ─── 自訂樣式 ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── 色票
       #e7ecef  淺灰（背景）   #274c77  深藍（主色）
       #6096ba  中藍（次要）   #a3cef1  淡藍（強調）
       #8b8c89  灰（輔助文字）
    ─────────────────────────────────────────────── */

    .stApp { background-color: #e7ecef; }
    #MainMenu, footer, header { visibility: hidden; }

    /* ── Hero ── */
    .hero {
        background: linear-gradient(135deg, #274c77 0%, #6096ba 100%);
        padding: 2rem 2.5rem; border-radius: 20px; color: #e7ecef;
        box-shadow: 0 10px 30px rgba(39,76,119,.35); margin-bottom: 1.5rem;
    }
    .hero h1 { font-size:2.5rem; margin:0; font-weight:700; color:#e7ecef; }
    .hero p  { font-size:1.05rem; opacity:.9; margin:.4rem 0 0 0; color:#a3cef1; }

    /* ── 區塊標題 ── */
    .section-title {
        font-size:1.4rem; font-weight:700; color:#274c77;
        margin:1rem 0 .8rem 0; padding-left:.8rem;
        border-left:5px solid #6096ba;
    }

    /* ── 天氣卡片 ── */
    .weather-card {
        background: linear-gradient(160deg,#fff 0%,#e7ecef 100%);
        padding:1.2rem; border-radius:16px; text-align:center;
        box-shadow:0 4px 14px rgba(39,76,119,.1); border:1px solid #a3cef1;
        transition:transform .2s,box-shadow .2s;
    }
    .weather-card:hover { transform:translateY(-4px); box-shadow:0 8px 24px rgba(39,76,119,.18); }
    .weather-card .date  { font-size:.85rem; color:#8b8c89; font-weight:600; }
    .weather-card .emoji { font-size:2.5rem; margin:.3rem 0; }
    .weather-card .wx    { font-size:.8rem;  color:#274c77; min-height:2.4em; }
    .weather-card .temp-max { color:#c0392b; font-size:1.5rem; font-weight:700; margin-top:.4rem; }
    .weather-card .temp-min { color:#6096ba; font-size:1rem;  font-weight:500; }

    /* ── Sidebar 背景 ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #274c77 0%, #1a3350 100%);
    }

    /* Sidebar：只針對 Markdown 容器的文字設白色，不碰按鈕 */
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] .stMarkdown h4,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown li,
    [data-testid="stSidebar"] .stMarkdown a {
        color: #e7ecef !important;
    }

    /* Sidebar 按鈕：淡藍背景 + 深藍文字 */
    [data-testid="stSidebar"] .stButton > button {
        background-color: #a3cef1 !important;
        border: none !important;
        border-radius: 10px !important;
        padding: .6rem 1rem !important;
        width: 100% !important;
    }
    /* 按鈕及其所有子元素強制深藍 */
    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] .stButton > button * {
        color: #274c77 !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover,
    [data-testid="stSidebar"] .stButton > button:hover * {
        background-color: #e7ecef !important;
        color: #274c77 !important;
    }
</style>
""", unsafe_allow_html=True)


# ─── 工具：天氣 emoji ───────────────────────────────────────────────────────
def weather_emoji(wx: str) -> str:
    if not wx:
        return "🌤️"
    if "雷" in wx:   return "⛈️"
    if "雨" in wx:   return "🌧️"
    if "雪" in wx:   return "❄️"
    if "陰" in wx:   return "☁️"
    if "多雲" in wx: return "⛅"
    if "晴" in wx:   return "☀️"
    return "🌤️"


def weather_color(wx: str) -> str:
    if not wx:             return "#8b8c89"
    if "雷" in wx:          return "#274c77"
    if "雨" in wx:          return "#6096ba"
    if "陰" in wx:          return "#8b8c89"
    if "多雲" in wx:        return "#6096ba"
    if "晴" in wx:          return "#c0392b"
    return "#8b8c89"


def match_coord(region_name: str):
    """把 CWA 回傳的地區名對到座標字典。"""
    for key, coord in REGION_COORDS.items():
        if key in region_name:
            return coord
    return None


# ─── 資料存取 ────────────────────────────────────────────────────────────────
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
    """抓每個地區日期最早的那筆（當作「今日」資料）給地圖用。"""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query('''
        SELECT t.regionName, t.dataDate, t.MaxT, t.MinT, t.weather
        FROM TemperatureForecasts t
        INNER JOIN (
            SELECT regionName, MIN(dataDate) AS minDate
            FROM TemperatureForecasts
            GROUP BY regionName
        ) m ON t.regionName = m.regionName AND t.dataDate = m.minDate
    ''', conn)
    conn.close()
    return df


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 控制台")
    st.markdown("---")

    if st.button("🔄  更新氣象資料"):
        with st.spinner('正在從中央氣象署抓取最新資料...'):
            result = subprocess.run(['python', 'weather_crawler.py'], capture_output=True, text=True)
            if result.returncode == 0:
                st.cache_data.clear()
                st.success("✅ 資料更新成功！")
            else:
                st.error("❌ 更新失敗")
                st.code(result.stderr)

    st.markdown("---")
    st.markdown("#### 📖 關於")
    st.markdown("""
    - 📡 資料來源：**中央氣象署**
    - 🕸️ API：`F-A0010-001`
    - 💾 儲存：`data.db` (SQLite3)
    - 🐍 框架：Streamlit + Folium
    """)


# ─── 主頁面 ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🌦️ 台灣一週氣象預報系統</h1>
    <p>即時掌握全台各分區天氣動態 ・ 資料來源：交通部中央氣象署</p>
</div>
""", unsafe_allow_html=True)


if not os.path.exists(DB_FILE):
    st.warning("⚠️ 目前無氣象資料，請點擊左側「更新氣象資料」以抓取最新預報。")
    st.stop()

regions = load_regions()
if not regions:
    st.warning("⚠️ 資料庫中無資料，請點擊左側「更新氣象資料」。")
    st.stop()


# ─── 區塊 1：台灣地圖 ────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🗺️ 全台分區即時概況</div>', unsafe_allow_html=True)

today_df = load_today_all_regions()

m = folium.Map(
    location=[23.7, 121.0],
    zoom_start=7,
    tiles='CartoDB positron',
)

for _, row in today_df.iterrows():
    coord = match_coord(row['regionName'])
    if coord is None:
        continue

    emoji = weather_emoji(row['weather'])
    color = weather_color(row['weather'])

    icon_html = f"""
    <div style="
        background: {color};
        color: white;
        border-radius: 50%;
        width: 64px; height: 64px;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        font-family: sans-serif;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        border: 3px solid white;
    ">
        <div style="font-size: 1.4rem; line-height: 1;">{emoji}</div>
        <div style="font-size: 0.75rem; font-weight: 700; line-height: 1.1;">{row['MaxT']}°/{row['MinT']}°</div>
    </div>
    """

    popup_html = f"""
    <div style="font-family: sans-serif; min-width: 150px;">
        <h4 style="margin:0 0 6px 0; color:{color};">{row['regionName']}</h4>
        <div>📅 {row['dataDate']}</div>
        <div>{emoji} {row['weather']}</div>
        <div>🌡️ 最高 <b style="color:#dc2626">{row['MaxT']}°C</b> / 最低 <b style="color:#2563eb">{row['MinT']}°C</b></div>
    </div>
    """

    folium.Marker(
        location=coord,
        icon=folium.DivIcon(html=icon_html, icon_size=(64, 64), icon_anchor=(32, 32)),
        popup=folium.Popup(popup_html, max_width=250),
        tooltip=row['regionName'],
    ).add_to(m)

st_folium(m, height=480, use_container_width=True, returned_objects=[])


# ─── 區塊 2：地區選擇與詳細 ─────────────────────────────────────────────────
st.markdown('<div class="section-title">📍 地區詳細預報</div>', unsafe_allow_html=True)

selected = st.selectbox("選擇想查詢的地區：", options=regions, label_visibility="collapsed")

if selected:
    df = load_region_data(selected)

    # ── 每日卡片 ──
    cols = st.columns(len(df))
    for idx, row in enumerate(df.itertuples()):
        with cols[idx]:
            date_str = row.dataDate[-5:].replace('-', '/')
            st.markdown(f"""
            <div class="weather-card">
                <div class="date">📅 {date_str}</div>
                <div class="emoji">{weather_emoji(row.weather)}</div>
                <div class="wx">{row.weather}</div>
                <div class="temp-max">🔺 {row.MaxT}°C</div>
                <div class="temp-min">🔻 {row.MinT}°C</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 折線圖 ──
    st.markdown('<div class="section-title">📈 氣溫趨勢圖</div>', unsafe_allow_html=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['dataDate'], y=df['MaxT'],
        mode='lines+markers+text',
        name='最高氣溫',
        line=dict(color='#c0392b', width=3, shape='spline'),
        marker=dict(size=12, color='#c0392b', line=dict(width=2, color='white')),
        text=[f"{t}°" for t in df['MaxT']],
        textposition='top center',
        textfont=dict(size=13, color='#c0392b'),
        fill='tonexty',
        fillcolor='rgba(163, 206, 241, 0.15)',
    ))
    fig.add_trace(go.Scatter(
        x=df['dataDate'], y=df['MinT'],
        mode='lines+markers+text',
        name='最低氣溫',
        line=dict(color='#6096ba', width=3, shape='spline'),
        marker=dict(size=12, color='#6096ba', line=dict(width=2, color='white')),
        text=[f"{t}°" for t in df['MinT']],
        textposition='bottom center',
        textfont=dict(size=13, color='#274c77'),
        fill='tozeroy',
        fillcolor='rgba(96, 150, 186, 0.08)',
    ))

    fig.update_layout(
        height=420,
        margin=dict(l=20, r=20, t=30, b=20),
        plot_bgcolor='rgba(231, 236, 239, 0.5)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode='x unified',
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
            font=dict(color='#274c77'),
        ),
        xaxis=dict(title='', showgrid=False, tickfont=dict(size=12, color='#274c77')),
        yaxis=dict(title='氣溫 (°C)', gridcolor='rgba(39,76,119,0.1)', tickfont=dict(size=12, color='#274c77')),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── 詳細表格 ──
    st.markdown('<div class="section-title">📊 詳細資料</div>', unsafe_allow_html=True)
    display_df = df.rename(columns={
        'dataDate': '日期',
        'weather':  '天氣概況',
        'MaxT':     '最高氣溫 (°C)',
        'MinT':     '最低氣溫 (°C)',
    })
    st.dataframe(display_df, use_container_width=True, hide_index=True)
