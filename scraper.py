import requests
from bs4 import BeautifulSoup
import csv
import json
import time
import urllib3

# Suppress insecure request warnings if verify=False is used
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = 'https://ssr1.scrape.center'

def scrape_page(page_url):
    print(f"Scraping: {page_url}")
    try:
        response = requests.get(page_url, verify=False, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {page_url}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    movies = []

    movie_cards = soup.select('.el-card.item')
    if not movie_cards:
        print(f"No movie cards found on {page_url}")
        
    for card in movie_cards:
        try:
            # 1. Title
            title_elem = card.select_one('h2.m-b-sm')
            title = title_elem.text.strip() if title_elem else ''

            # 2. Detail URL
            link_elem = card.select_one('a.name')
            detail_url = BASE_URL + link_elem['href'] if link_elem and 'href' in link_elem.attrs else ''

            # 3. Image
            img_elem = card.select_one('.cover')
            image_url = img_elem['src'] if img_elem and 'src' in img_elem.attrs else ''

            # 4. Categories
            category_elems = card.select('.categories span')
            categories = ','.join([cat.text.strip() for cat in category_elems])

            # 5. Region & Duration, 6. Release Date
            info_divs = card.select('.m-v-sm.info')
            region = ''
            duration = ''
            release_date = ''
            
            if len(info_divs) >= 1:
                spans = info_divs[0].find_all('span')
                if len(spans) >= 3:
                    region = spans[0].text.strip()
                    duration = spans[2].text.strip()
                elif len(spans) == 1:
                    region = spans[0].text.strip()
            
            if len(info_divs) >= 2:
                date_span = info_divs[1].find('span')
                if date_span:
                    release_date = date_span.text.strip()
            
            # 7. Score
            score_elem = card.select_one('.score')
            score = score_elem.text.strip() if score_elem else ''

            movie_data = {
                'title': title,
                'detail_url': detail_url,
                'image': image_url,
                'categories': categories,
                'region': region,
                'duration': duration,
                'release_date': release_date,
                'score': score
            }
            movies.append(movie_data)

        except Exception as e:
            print(f"Error parsing a movie card: {e}")
            continue

    return movies

def main():
    all_movies = []
    
    for page in range(1, 11):
        url = f'{BASE_URL}/page/{page}'
        movies = scrape_page(url)
        all_movies.extend(movies)
        # Sleep to avoid rapid requests as per guidelines
        time.sleep(1)
        
    # Save to CSV
    csv_file = 'movies.csv'
    csv_headers = ['title', 'detail_url', 'image', 'categories', 'region', 'duration', 'release_date', 'score']
    
    try:
        with open(csv_file, mode='w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=csv_headers)
            writer.writeheader()
            writer.writerows(all_movies)
        print(f"Successfully saved data for {len(all_movies)} movies to {csv_file}")
    except Exception as e:
        print(f"Error saving CSV: {e}")

    # Bonus: Save to JSON
    json_file = 'movies.json'
    try:
        with open(json_file, mode='w', encoding='utf-8') as f:
            json.dump(all_movies, f, indent=4, ensure_ascii=False)
        print(f"Bonus: Successfully saved data to {json_file}")
    except Exception as e:
        print(f"Error saving JSON: {e}")

if __name__ == '__main__':
    main()
