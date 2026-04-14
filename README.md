# 台灣各分區一週氣象預報系統 (CWA Weather Forecast System)

這是一個利用 Python 從「交通部中央氣象署 (CWA) 開放資料平台」抓取氣象預報資料，並透過 Streamlit 提供無違和視覺化操作介面的專案。

## 🌟 系統功能特色

1. **氣象資料自動爬蟲**
   - 透過 `weather_crawler.py` 向中央氣象署 API (F-A0010-001) 請求各地區一週氣象預報。
   - 解析複雜的 JSON 結構，並自動過濾成簡潔明瞭的 CSV 資料格式。
   - 包含各地區逐日的：天氣概況、最高溫、最低溫。

2. **動態 Web 視覺化介面**
   - 透過 `app.py` (Streamlit 建構) 將靜態的 CSV 資料轉化為互動式網頁。
   - 支援「選擇地區」下拉式選單 (如：北部、中部、南部、東部等)。
   - 提供「未來一週天氣概況」卡片介面排版。
   - 提供單鍵背景執行爬蟲更新 (Refresh) 的功能。
   - 可展開檢視完整詳細歷史數據。

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
   > 註：`.env` 與生成的 `weather_data.csv` 已加入 `.gitignore`，以確保您的金鑰安全。

## 🏃 執行方式

### 方案 A：直接啟動 Web 介面 (推薦)
啟動 Streamlit 伺服器，介面中已包含觸發資料爬取的按鈕：
```bash
streamlit run app.py
```
*(啟動後請依提示開啟瀏覽器輸入 `http://localhost:8501` 查看結果)*

### 方案 B：單獨執行爬蟲程式
若您只需要最新的資料 CSV 檔供其它用途，可以直接執行：
```bash
python weather_crawler.py
```
執行後將會在目錄中產生（或覆蓋） `weather_data.csv`。
