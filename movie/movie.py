from ariadne import graphql_sync, make_executable_schema, load_schema_from_path, ObjectType, QueryType, MutationType
from flask import Flask, request, jsonify, make_response
import json
import os
from pymongo import MongoClient

# Configuration centralisée
USE_MONGO = os.getenv("USE_MONGO", "false").lower() == "true"
USE_DOCKER = os.getenv("USE_DOCKER", "false").lower() == "true"
MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017/archiDistriDB")


# Connexion à MongoDB si nécessaire
if USE_MONGO:
    client = MongoClient(MONGO_URL)
    db = client["archiDistriDB"]
    movies_collection = db["movies"]
    actors_collection = db["actors"]

PORT = 3200
HOST = '0.0.0.0'
app = Flask(__name__)

# Définition des types GraphQL
actor = ObjectType('Actor')
query = QueryType()
movie = ObjectType('Movie')
mutation = MutationType()

# Définition des résolveurs
def movie_with_id(_, info, _id):
    if USE_MONGO:
        movie = movies_collection.find_one({"id": int(_id)})
        return movie
    else:
        with open('./data/movies.json', "r") as file:
            movies = json.load(file)
            for movie in movies['movies']:
                if movie['id'] == int(_id):
                    return movie
        return None

def update_movie_rate(_, info, _id, _rate):
    if USE_MONGO:
        movies_collection.update_one(
            {"id": int(_id)},
            {"$set": {"rating": float(_rate)}}
        )
        return movies_collection.find_one({"id": int(_id)})
    else:
        newmovies = {}
        newmovie = {}
        with open('./data/movies.json', "r") as rfile:
            movies = json.load(rfile)
            for movie in movies['movies']:
                if movie['id'] == int(_id):
                    movie['rating'] = float(_rate)
                    newmovie = movie
                    newmovies = movies
        with open('./data/movies.json', "w") as wfile:
            json.dump(newmovies, wfile)
        return newmovie

def resolve_actors_in_movie(movie, info):
    if USE_MONGO:
        actors = list(actors_collection.find({"films": movie["id"]}))
        return actors
    else:
        with open('./data/actors.json', "r") as file:
            actors = json.load(file)
            result = [actor for actor in actors['actors'] if movie['id'] in actor['films']]
            return result

# Configuration des résolveurs
query.set_field('movie_with_id', movie_with_id)
mutation.set_field('update_movie_rate', update_movie_rate)
movie.set_field('actors', resolve_actors_in_movie)

# Chargement du schéma GraphQL
type_defs = load_schema_from_path('movie.graphql')
schema = make_executable_schema(type_defs, movie, query, mutation, actor)

# Route d'accueil
@app.route("/", methods=['GET'])
def home():
    return make_response("<h1 style='color:blue'>Welcome to the Movie service!</h1>", 200)

# Point d'entrée GraphQL
@app.route('/graphql', methods=['POST'])
def graphql_server():
    data = request.get_json()
    success, result = graphql_sync(
        schema,
        data,
        context_value=None,
        debug=app.debug
    )
    status_code = 200 if success else 400
    return jsonify(result), status_code

if __name__ == "__main__":
    print(f"Server running on port {PORT}")
    app.run(host=HOST, port=PORT)
