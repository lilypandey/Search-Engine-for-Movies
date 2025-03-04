from flask import Flask, render_template, request, jsonify
from script import MovieManager

app = Flask(__name__)
movie_manager = MovieManager()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip().lower()
    results = movie_manager.cached_data(query)
    return render_template('home.html', movies=results)

@app.route('/top250', methods=['GET'])
def top_250():
    top_movies = movie_manager.fetch_imdb_top_250()
    return render_template('home.html', top_movies=top_movies)

if __name__ == "__main__":
    app.run(debug=True)
