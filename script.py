import requests
import sqlite3
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MovieManager:
    def __init__(self, db_name='movies.db'):
        self.db_name = db_name
        load_dotenv()
        self.api_key = os.getenv('OMDB_API_KEY')
        self.sqlite_db()

    def fetch_api_requests(self, title, type=None):
        try:
            url = f"http://www.omdbapi.com/?apikey={self.api_key}&s={title}"
            params = {'s': title}
            if type:
                params['type'] = type
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("Response") == "True":
                    return data['Search']
            logging.warning(f"API request failed with response: {response.text if hasattr(response, 'text') else 'No response text'}")
        except Exception as e:
            logging.error(f"Error in fetch_api_requests: {str(e)}")
        return None

    def sqlite_db(self):
        try:
            with sqlite3.connect(self.db_name) as connection:
                cursor = connection.cursor()
                cursor.execute('''CREATE TABLE IF NOT EXISTS movies (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                Title TEXT,
                                Year TEXT,
                                imdbID TEXT UNIQUE,
                                Type TEXT,
                                Poster TEXT)''')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_title ON movies(Title)')
                
                # Create table for IMDb Top 250
                cursor.execute('''CREATE TABLE IF NOT EXISTS top250 (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                title TEXT,
                                link TEXT)''')
                connection.commit()
        except Exception as e:
            logging.error(f"Error in sqlite_db: {str(e)}")

    def insert_movies_into_db(self, movies_data):
        try:
            with sqlite3.connect(self.db_name) as connection:
                cursor = connection.cursor()
                for movie in movies_data:
                    cursor.execute('SELECT imdbID FROM movies WHERE imdbID=?', (movie['imdbID'],))
                    if cursor.fetchone() is None:
                        cursor.execute('''INSERT INTO movies (Title, Year, imdbID, Type, Poster)
                                        VALUES (?, ?, ?, ?, ?)''',
                                    (movie['Title'], movie['Year'], movie['imdbID'], movie['Type'], movie['Poster']))
                connection.commit()
        except Exception as e:
            logging.error(f"Error in insert_movies_into_db: {str(e)}")

    def cached_data(self, title, type=None):
        try:
            with sqlite3.connect(self.db_name) as connection:
                cursor = connection.cursor()
                query = 'SELECT * FROM movies WHERE Title LIKE ?'
                params = (f"%{title}%",)
                if type:
                    query += ' AND Type=?'
                    params += (type,)
                cursor.execute(query, params)
                result = cursor.fetchall()
                if result:
                    return result
                
                # If not found in cache, fetch from API
                movies_data = self.fetch_api_requests(title, type)
                if movies_data:
                    self.insert_movies_into_db(movies_data)
                    cursor.execute(query, params)
                    return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error in cached_data: {str(e)}")
        return []

    def fetch_top_250(self):
        # Try to get from cache first
        cached_movies = self.get_cached_top250()
        if cached_movies and len(cached_movies) > 0:
            logging.info(f"Returning {len(cached_movies)} movies from cache")
            return cached_movies
            
        # If not in cache, scrape using the method provided by user
        logging.info("Scraping IMDb Top 250...")
        
        # Initialize options

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        try:
            # Initialize driver
            service = Service()
            driver = webdriver.Chrome(service=service, options=options)
            
            url = "https://www.imdb.com/chart/top/"
            driver.get(url)
            
            # Wait for content to load
            time.sleep(3)
            
            # Find all <a> tags that contain the movie links and titles
            elements = driver.find_elements(By.CSS_SELECTOR, "a.ipc-title-link-wrapper")
            
            logging.info(f"Found {len(elements)} movie elements")
            
            # Build dictionary: { 'Movie Title': 'Full IMDb URL' }
            movies = {}
            
            for el in elements:
                try:
                    title_tag = el.find_element(By.CSS_SELECTOR, "h3.ipc-title__text")
                    title = title_tag.text.strip() 
                    href = el.get_attribute("href")  # Full URL
                    if title and href:
                        movies[title] = href
                except Exception as e:
                    logging.error(f"Error processing element: {str(e)}")
                    continue
            
            logging.info(f"Successfully processed {len(movies)} movies")
            
            # Save to cache if we found movies
            if movies:
                self.cache_top250(movies)
                return movies
            else:
                logging.warning("No movies extracted from IMDb Top 250 page")
                return {}
                
        except Exception as e:
            logging.error(f"Error in fetch_top_250: {str(e)}")
            return {}
        finally:
            if 'driver' in locals():
                driver.quit()
            
    def cache_top250(self, movies):
        try:
            with sqlite3.connect(self.db_name) as connection:
                cursor = connection.cursor()
                # Clear existing data
                cursor.execute('DELETE FROM top250')
                
                # Insert new data
                for title, link in movies.items():
                    cursor.execute('INSERT INTO top250 (title, link) VALUES (?, ?)', (title, link))
                connection.commit()
                logging.info(f"Cached {len(movies)} movies in the database")
        except Exception as e:
            logging.error(f"Error in cache_top250: {str(e)}")
    
    def get_cached_top250(self):
        try:
            with sqlite3.connect(self.db_name) as connection:
                cursor = connection.cursor()
                cursor.execute('SELECT title, link FROM top250')
                results = cursor.fetchall()
                if results:
                    return {title: link for title, link in results}
                return {}
        except Exception as e:
            logging.error(f"Error in get_cached_top250: {str(e)}")
            return {}