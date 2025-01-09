import requests
import json
import sqlite3
from dotenv import load_dotenv
import os

class MovieManager:
    def __init__(self, db_name='movies.db'):
        self.db_name = db_name
        load_dotenv()
        self.api_key = os.getenv('OMDB_API_KEY')
        self.sqlite_db()

    def fetch_api_requests(self, title, type=None):
        url = "http://www.omdbapi.com/?apikey=" + self.api_key
        params = {'s': title}
        if type:
            params['type'] = type
        response =  requests.get(url, params=params)
        if response.status_code==200:
            data = response.json()
            if data.get("Response")=="True":
                print("Data retreived from API")
                return data['Search']
            else:
                print(f"Error: {data.get('Error')}")
                return None
        
        else:
            print(f"Error fetching data from API. Error code: {response.status_code}")
            return None

    def sqlite_db(self):
        with sqlite3.connect(self.db_name) as connection:
            cursor = connection.cursor()
            table= '''
            CREATE TABLE IF NOT EXISTS movies(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Title TEXT,
            Year TEXT,
            imdbID TEXT UNIQUE,
            Type TEXT,
            Poster TEXT
            );'''
            cursor.execute(table)
       
            index_query = '''CREATE INDEX IF NOT EXISTS idx_title ON movies(Title);'''
            cursor.execute(index_query)

            connection.commit()
            print("Table created successfully or already exists.")


    def insert_movies_into_db(self, movies_data):
        with sqlite3.connect(self.db_name) as connection:
            cursor = connection.cursor()

            for movie in movies_data:
                cursor.execute('SELECT imdbID FROM MOVIES WHERE imdbID=?', (movie['imdbID'],))

                if cursor.fetchone() is None:
                    cursor.execute('''
                    INSERT INTO  movies(Title, Year, imdbID, Type, Poster)
                    VALUES(?, ?, ?, ?, ?)
                    ''',
                    (movie['Title'],
                    movie['Year'],
                    movie['imdbID'],
                    movie['Type'],
                    movie['Poster']))

            connection.commit()

    def cached_data(self, title, type=None):
        with sqlite3.connect(self.db_name) as connection:
            cursor = connection.cursor()

            if type:
                cursor.execute('SELECT *FROM MOVIES WHERE Title=? AND Type=?', (title, type))
        
            else:
                cursor.execute('SELECT *FROM MOVIES WHERE Title=?', (title,))

            result = cursor.fetchall()

            if result:
                return result

            else:
                movies_data = self.fetch_api_requests(title, type)
                if movies_data:
                    self.insert_movies_into_db(movies_data)
                    if type:
                        cursor.execute('SELECT *FROM MOVIES WHERE Title=? AND Type=?', (title, type))
                    else:
                        cursor.execute('SELECT *FROM MOVIES WHERE Title=?', (title,))

                    return cursor.fetchall()
                
                else:
                    return None
