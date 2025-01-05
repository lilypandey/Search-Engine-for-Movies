from flask import Flask, render_template, request
from script import MovieManager

app=Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/search', methods = ['GET'])
def search():
    query = request.args.get('query','').lower()
    movie_manager = MovieManager()
    results = movie_manager.cached_data(query)

    return render_template('home.html', movies=results)

if __name__ == "__main__":
    app.run(debug="True")