import urllib.request
import json
import csv
import ssl
import os
from dotenv import load_dotenv

load_dotenv()

def fetch_weather_data():
    token = os.getenv('CWA_API_TOKEN')
    if not token:
        print("Error: API token not found in .env file.")
        return None
    url = f'https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/F-A0010-001?Authorization={token}&downloadType=WEB&format=JSON'
    
    # Create an unverified SSL context to avoid certificate verification errors
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def process_and_save_data(data, output_file='weather_data.csv'):
    try:
        locations = data['cwaopendata']['resources']['resource']['data']['agrWeatherForecasts']['weatherForecasts']['location']
        
        # Prepare CSV rows
        csv_data = []
        headers = ['Location', 'Date', 'Weather', 'Max_Temperature', 'Min_Temperature']
        csv_data.append(headers)
        
        for loc in locations:
            location_name = loc['locationName']
            we = loc['weatherElements']
            
            wx_daily = we.get('Wx', {}).get('daily', [])
            maxt_daily = we.get('MaxT', {}).get('daily', [])
            mint_daily = we.get('MinT', {}).get('daily', [])
            
            # Assuming all daily lists have the same length and correspond to the same dates
            for wx, maxt, mint in zip(wx_daily, maxt_daily, mint_daily):
                date = wx['dataDate']
                weather = wx['weather']
                max_t = maxt['temperature']
                min_t = mint['temperature']
                
                csv_data.append([location_name, date, weather, max_t, min_t])
                
        # Write to CSV
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)
            
        print(f"Data successfully saved to {output_file}")
        
    except KeyError as e:
        print(f"Error parsing data structure (missing key): {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    print("Fetching weather data...")
    data = fetch_weather_data()
    if data:
        process_and_save_data(data)
