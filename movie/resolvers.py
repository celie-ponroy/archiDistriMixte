import json
import os
from pymongo import MongoClient

USE_MONGO = os.getenv("USE_MONGO", "false").lower() == "true"
USE_DOCKER = os.getenv("USE_DOCKER", "false").lower() == "true"
MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017/archiDistriDB")

if USE_MONGO:
    client = MongoClient(MONGO_URL)
    db = client["archiDistriDB"]
    movies_collection = db["movies"]
    actors_collection = db["actors"]
    
    if movies_collection.count_documents({}) == 0:
        with open('./data/movies.json', 'r') as jsf:
            initial_movies = json.load(jsf)["movies"]
            movies_collection.insert_many(initial_movies)
        movies = list(movies_collection.find({}))
    else:
        with open('./data/movies.json', "r") as jsf:
            movies = json.load(jsf)["movies"]
    
    if actors_collection.count_documents({}) == 0:
        with open('./data/actors.json', 'r') as jsf:
            initial_actors = json.load(jsf)["actors"]
            actors_collection.insert_many(initial_actors)
        actors = list(actors_collection.find({}))
    else:
        with open('./data/actors.json', "r") as jsf:
            actors = json.load(jsf)["actors"]

def movie_with_id(_,info,_id):
    if USE_MONGO:
            movie = movies_collection.find_one({"id": _id})
            return movie
    else:
        with open('{}/data/movies.json'.format("."), "r") as file:
            movies = json.load(file)
            for movie in movies['movies']:
                if movie['id'] == _id:
                    return movie
                
def update_movie_rate(_,info,_id,_rate):
    newmovies = {}
    newmovie = {}
    if USE_MONGO:
        movies_collection.update_one(
            {"id": _id},
            {"$set": {"rating": float(_rate)}}
        )
        return movies_collection.find_one({"id": _id})
    else:
        with open('{}/data/movies.json'.format("."), "r") as rfile:
            movies = json.load(rfile)
            for movie in movies['movies']:
                if movie['id'] == _id:
                    movie['rating'] = _rate
                    newmovie = movie
                    newmovies = movies
        with open('{}/data/movies.json'.format("."), "w") as wfile:
            json.dump(newmovies, wfile)
        return newmovie

def resolve_actors_in_movie(movie, info):
    if USE_MONGO:
        actors = list(actors_collection.find({"films": movie["id"]}))
        return actors
    else:
        with open('{}/data/actors.json'.format("."), "r") as file:
            actors = json.load(file)
            result = [actor for actor in actors['actors'] if movie['id'] in actor['films']]
            return result