import requests
import sqlite3
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class MovieManager:
    def __init__(self, db_name='movies.db'):
        self.db_name = db_name
        load_dotenv()
        self.api_key = os.getenv('OMDB_API_KEY')
        self.sqlite_db()

    def fetch_api_requests(self, title, type=None):
        url = f"http://www.omdbapi.com/?apikey={self.api_key}&s={title}"
        params = {'s': title}
        if type:
            params['type'] = type
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("Response") == "True":
                return data['Search']
        return None

    def sqlite_db(self):
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
            connection.commit()

    def insert_movies_into_db(self, movies_data):
        with sqlite3.connect(self.db_name) as connection:
            cursor = connection.cursor()
            for movie in movies_data:
                cursor.execute('SELECT imdbID FROM movies WHERE imdbID=?', (movie['imdbID'],))
                if cursor.fetchone() is None:
                    cursor.execute('''INSERT INTO movies (Title, Year, imdbID, Type, Poster)
                                      VALUES (?, ?, ?, ?, ?)''',
                                   (movie['Title'], movie['Year'], movie['imdbID'], movie['Type'], movie['Poster']))
            connection.commit()

    def cached_data(self, title, type=None):
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
            movies_data = self.fetch_api_requests(title, type)
            if movies_data:
                self.insert_movies_into_db(movies_data)
                cursor.execute(query, params)
                return cursor.fetchall()
            return None

    def fetch_imdb_top_250(self):
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        driver.get("https://www.imdb.com/chart/top/")
        movies = driver.find_elements(By.XPATH, "//td[@class='titleColumn']/a")
        top_movies = [movie.text for movie in movies]
        driver.quit()
        return top_movies

