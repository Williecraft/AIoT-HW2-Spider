import requests
import json
import csv
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = 'data'
DB_FILE = os.path.join(DATA_DIR, 'data.db')
CSV_FILE = os.path.join(DATA_DIR, 'weather_data.csv')


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

# ── HW2-1：調用 CWA API 獲取天氣預報資料 ──────────────────────────────────────

def fetch_weather_data():
    token = os.getenv('CWA_API_TOKEN')
    if not token:
        print("Error: API token not found in .env file.")
        return None

    url = (
        f'https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/F-A0010-001'
        f'?Authorization={token}&downloadType=WEB&format=JSON'
    )

    try:
        response = requests.get(url, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        data = response.json()

        # HW2-1：觀察原始 JSON 資料（只印前 500 字避免輸出過長）
        raw_str = json.dumps(data, ensure_ascii=False, indent=2)
        print("=== HW2-1：原始 JSON 資料（前 500 字）===")
        print(raw_str[:500])
        print("...\n")

        return data
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None


# ── HW2-2：分析資料，提取最高與最低氣溫 ──────────────────────────────────────

def extract_temperature_data(data):
    locations = data['cwaopendata']['resources']['resource']['data']['agrWeatherForecasts']['weatherForecasts']['location']

    extracted = []
    for loc in locations:
        region = loc['locationName']
        we = loc['weatherElements']

        wx_daily   = we.get('Wx',   {}).get('daily', [])
        maxt_daily = we.get('MaxT', {}).get('daily', [])
        mint_daily = we.get('MinT', {}).get('daily', [])

        for wx, maxt, mint in zip(wx_daily, maxt_daily, mint_daily):
            extracted.append({
                'regionName': region,
                'dataDate':   wx['dataDate'],
                'weather':    wx['weather'],
                'MaxT':       int(maxt['temperature']),
                'MinT':       int(mint['temperature']),
            })

    # HW2-2：觀察提取的氣溫資料
    print("=== HW2-2：提取的氣溫資料 ===")
    print(json.dumps(extracted, ensure_ascii=False, indent=2))
    print()

    return extracted


# ── HW2-3：將氣溫資料儲存到 SQLite3 資料庫 ───────────────────────────────────

def save_to_sqlite(records, db_file=DB_FILE):
    ensure_data_dir()
    conn = sqlite3.connect(db_file)
    cur  = conn.cursor()

    cur.execute('DROP TABLE IF EXISTS TemperatureForecasts')
    cur.execute('''
        CREATE TABLE TemperatureForecasts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            regionName TEXT,
            dataDate   TEXT,
            MaxT       INTEGER,
            MinT       INTEGER,
            weather    TEXT
        )
    ''')

    for r in records:
        cur.execute(
            'INSERT INTO TemperatureForecasts (regionName, dataDate, MaxT, MinT, weather) VALUES (?, ?, ?, ?, ?)',
            (r['regionName'], r['dataDate'], r['MaxT'], r['MinT'], r['weather'])
        )

    conn.commit()
    print(f"=== HW2-3：資料已儲存至 {db_file} ===\n")

    # 驗證一：列出所有地區名稱
    print("--- 查詢：所有地區名稱 ---")
    for row in cur.execute('SELECT DISTINCT regionName FROM TemperatureForecasts'):
        print(row[0])

    # 驗證二：列出中部地區的氣溫資料
    print("\n--- 查詢：中部地區氣溫資料 ---")
    for row in cur.execute("SELECT * FROM TemperatureForecasts WHERE regionName LIKE '%中部%'"):
        print(row)

    conn.close()


# ── 次要輸出：保留 CSV（供參考） ─────────────────────────────────────────────

def save_to_csv(records, output_file=CSV_FILE):
    ensure_data_dir()
    headers = ['Location', 'Date', 'Weather', 'Max_Temperature', 'Min_Temperature']
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for r in records:
            writer.writerow([r['regionName'], r['dataDate'], r['weather'], r['MaxT'], r['MinT']])
    print(f"\nCSV 也已儲存至 {output_file}")


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("正在從中央氣象署抓取資料...\n")
    data = fetch_weather_data()
    if data:
        records = extract_temperature_data(data)
        save_to_sqlite(records)
        save_to_csv(records)
