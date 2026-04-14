import streamlit as st
import pandas as pd
import os
import subprocess

# Ensure page layout is wide for better viewing
st.set_page_config(page_title="氣象預報查詢系統", layout="wide")

# App title and styling
st.title("🌦️ 台灣各分區一週氣象預報系統")
st.markdown("您可以透過左側表單選擇區域，檢視該地區未來的氣象概況。")

DATA_FILE = 'weather_data.csv'

# Function to run the crawler
def update_data():
    with st.spinner('正在從中央氣象署抓取最新資料...'):
        try:
            result = subprocess.run(['python', 'weather_crawler.py'], capture_output=True, text=True)
            if result.returncode == 0:
                st.success("✅ 資料更新成功！")
            else:
                st.error("❌ 更新失敗，請檢查 Token 或是網路連線。")
                st.error(result.stderr)
        except Exception as e:
            st.error(f"執行爬蟲時發生錯誤: {e}")

# Sidebar controls
st.sidebar.header("設定")
if st.sidebar.button("🔄 更新氣象資料"):
    update_data()

# Data loading
@st.cache_data(ttl=600)  # cache the data for 10 minutes
def load_data():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame() # empty Df
    return pd.read_csv(DATA_FILE)

df = load_data()

if df.empty:
    st.warning("⚠️ 目前無氣象資料，請點擊左側「更新氣象資料」以抓取最新預報。")
else:
    # Region Selection
    locations = df['Location'].unique().tolist()
    
    selected_location = st.selectbox(
        "📍 選擇地區",
        options=locations,
        index=0 if locations else None
    )
    
    if selected_location:
        # Filter data for selected location
        loc_df = df[df['Location'] == selected_location].copy()
        
        # Display nicely in metric cards
        st.subheader(f"📅 {selected_location} - 未來一週天氣概況")
        
        # Streamlit columns are great for scrolling cards
        cols = st.columns(len(loc_df))
        
        for idx, row in enumerate(loc_df.itertuples()):
            # Parse simple date string (assuming format 'YYYY-MM-DD')
            date_str = row.Date[-5:] # just take MM-DD
            
            with cols[idx]:
                st.markdown(f"**{date_str}**")
                
                # Determine weather emoji vaguely based on keyword
                wx = row.Weather
                emoji = "🌤️"
                if "雨" in wx:
                    emoji = "🌧️"
                elif "陰" in wx:
                    emoji = "☁️"
                elif "晴" in wx:
                    emoji = "☀️"
                    
                st.metric(label=f"{emoji} {wx}", value=f"{row.Max_Temperature}°C", delta=f"低溫 {row.Min_Temperature}°C", delta_color="off")

        # Detailed Expander
        st.write("---")
        with st.expander("📊 點擊檢視詳細資料 (隱藏/展開)"):
            st.dataframe(loc_df, use_container_width=True, hide_index=True)
