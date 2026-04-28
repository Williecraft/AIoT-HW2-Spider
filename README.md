# 台灣各分區一週氣象預報系統 (CWA Weather Forecast System)

🌐 **Streamlit Cloud Demo：** https://williecraft-aiot-hw2-spider.streamlit.app

![專案首頁概覽](docs/report_images/project_homepage_overview.png)

這是一個利用 Python 從「交通部中央氣象署 (CWA) 開放資料平台」抓取氣象預報資料，並透過 Streamlit 提供無違和視覺化操作介面的專案。

## 🌟 系統功能特色

1. **氣象資料自動爬蟲**
   - 透過 `weather_crawler.py` 向中央氣象署 API (F-A0010-001) 請求各地區一週氣象預報。
   - 解析複雜的 JSON 結構，提取各分區逐日的天氣概況、最高溫與最低溫。
   - 主要資料儲存於 `data/data.db`，並額外輸出 `data/weather_data.csv` 作為檢查用資料。

2. **動態 Web 視覺化介面**
   - 透過 `app.py` (Streamlit 建構) 從 SQLite 資料庫查詢資料並呈現互動式網頁。
   - 支援「選擇地區」下拉式選單 (如：北部、中部、南部、東部等)。
   - 提供台灣六大分區地圖、每日天氣卡片、氣溫折線圖與詳細資料表。
   - 提供單鍵背景執行爬蟲更新 (Refresh) 的功能。

## 🚀 環境安裝與設定

1. **安裝依賴套件**
   請確保您的環境已經安裝 Python，然後執行：
   ```bash
   pip install -r requirements.txt
   ```

2. **設定環境變數 (.env)**
   為了避免 API Token 外流，本專案使用 `python-dotenv` 管理金鑰。
   請在專案根目錄建立 `.env` 檔案，並填入您在[中央氣象署開放資料平台](https://opendata.cwa.gov.tw/)申請的授權碼：
   ```env
   CWA_API_TOKEN=您的氣象署_API_授權碼
   ```
   > 註：`.env` 與執行產生的資料檔已加入 `.gitignore`，以確保金鑰安全並保持專案整潔。

## 🏃 執行方式

### 方案 A：直接啟動 Web 介面 (推薦)
啟動 Streamlit 伺服器，介面中已包含觸發資料爬取的按鈕：
```bash
streamlit run app.py
```
*(啟動後請依提示開啟瀏覽器輸入 `http://localhost:8501` 查看結果)*

### 方案 B：單獨執行爬蟲程式
若您只需要重新抓取與整理最新資料，可以直接執行：
```bash
python weather_crawler.py
```
執行後將會更新 `data/data.db`，並同步輸出 `data/weather_data.csv`。
