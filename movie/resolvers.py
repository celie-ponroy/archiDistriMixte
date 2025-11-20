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

def movies(_,info):
    if USE_MONGO:
            movie = movies_collection.find(({}))
            return movie
    else:
        with open('{}/data/movies.json'.format("."), "r") as file:
            movies = json.load(file)
            return movies

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
                
def movie_with_title(_, info, title):
    if USE_MONGO:
        movie = movies_collection.find_one({"title": title})
        return movie
    else:
        with open('./data/movies.json', "r") as file:
            data = json.load(file)
            for movie in data["movies"]:
                if movie["title"] == title:
                    return movie
        return None


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

def create_movie(_, info, id, title, director, rating, actors=None):
    if actors is None:
        actors = []

    new_movie = {
        "id": id,
        "title": title,
        "director": director,
        "rating": float(rating),
        "actors": actors
    }

    if USE_MONGO:
        movies_collection.insert_one(new_movie)
        return new_movie
    
    else:
        with open('./data/movies.json', "r") as rfile:
            data = json.load(rfile)

        data["movies"].append(new_movie)

        with open('./data/movies.json', "w") as wfile:
            json.dump(data, wfile, indent=4)

        return new_movie

def delete_movie(_, info, id):
    if USE_MONGO:
        result = movies_collection.delete_one({"id": id})
        return result.deleted_count > 0
    
    else:
        with open('./data/movies.json', "r") as rfile:
            data = json.load(rfile)

        before = len(data["movies"])
        data["movies"] = [m for m in data["movies"] if m["id"] != id]
        after = len(data["movies"])

        with open('./data/movies.json', "w") as wfile:
            json.dump(data, wfile, indent=4)

        return after < before
