from flask import Flask, render_template, request, jsonify
from script import MovieManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
movie_manager = MovieManager()

@app.route('/')
def home():
    logging.info("Home route accessed, fetching top 250 movies...")
    top_movies = movie_manager.fetch_top_250()
    logging.info(f"Fetched {len(top_movies)} top movies")
    return render_template('home.html', top_movies=top_movies)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip().lower()
    logging.info(f"Search route accessed with query: {query}")
    results = movie_manager.cached_data(query)
    return render_template('home.html', movies=results)

@app.route('/search_top250', methods=['GET'])
def search_top250():
    query = request.args.get('query', '').strip().lower()
    logging.info(f"Search top 250 route accessed with query: {query}")
    top_movies = movie_manager.fetch_top_250()
    filtered = {title: link for title, link in top_movies.items() if query in title.lower()}
    return render_template('home.html', top_movies=filtered)

if __name__ == "__main__":
    app.run(debug=True)