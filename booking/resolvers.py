import json
import os

import requests 
import grpc
from protos import schedule_pb2, schedule_pb2_grpc
from pymongo import MongoClient


USE_MONGO = os.getenv("USE_MONGO", "false").lower() == "true"
USE_DOCKER = os.getenv("USE_DOCKER", "false").lower() == "true"
MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017/archiDistriDB")
if USE_DOCKER:
    USER_SERVICE_URL = "http://user:3203"
    MOVIE_SERVICE_URL = "http://movie:3200/graphql"
else:
    USER_SERVICE_URL = "http://localhost:3203" 
    MOVIE_SERVICE_URL = "http://localhost:3200/graphql" 

if USE_DOCKER:
    SCHEDULE_GRPC_URL = "schedule:50051"
else:
    SCHEDULE_GRPC_URL = "localhost:50051"

#connection à mongo 
if USE_MONGO:
    client = MongoClient(MONGO_URL)
    db = client["archiDistriDB"]
    bookings_collection = db["bookings"]

    if bookings_collection.count_documents({}) == 0:
        with open('./data/bookings.json', 'r') as jsf:
            initial_bookings = json.load(jsf)["bookings"]
            bookings_collection.insert_many(initial_bookings)
    else:
        with open('./data/bookings.json', "r") as jsf:
            bookings = json.load(jsf)["bookings"]
    


def is_movie_scheduled(date: str, movie_id: str) -> bool:
    # Return true si le movie existe à la bonne date
    with grpc.insecure_channel(SCHEDULE_GRPC_URL) as channel:
        stub = schedule_pb2_grpc.ScheduleStub(channel)
        schedule = stub.GetScheduleByDate(schedule_pb2.ScheduleDate(date=date))
        return movie_id in schedule.movies


def booking_with_id(_, info, userid):
    # Récupérer l'utilisateur courant depuis le contexte
    requester_id = info.context.headers.get("X-User-Id")
    if not requester_id:
        raise Exception("Utilisateur non authentifié")
    print(requester_id)
    # Appel microservice User
    user_response = requests.get(f"{USER_SERVICE_URL}/users/{requester_id}")
    if user_response.status_code != 200:
        raise Exception("Utilisateur courant introuvable")
    user = user_response.json()

    is_admin = user.get("admin", False)
    is_owner = str(requester_id) == str(userid)

    if not (is_admin or is_owner):
        raise Exception("Accès refusé : seuls les admins ou le propriétaire peuvent accéder aux bookings")
    # Lecture des bookings
    if USE_MONGO:
        bookings_collection = db["bookings"]
        user_bookings = bookings_collection.find({"userid": userid})
        result = []
        for booking in user_bookings:
            for date_entry in booking.get("dates", []):
                date_str = date_entry.get("date")
                for movie_id in date_entry.get("movies", []):
                    result.append({
                        "userid": userid,
                        "movieId": movie_id,
                        "showtime": date_str
                    })
        return result
    else:
        with open('./data/bookings.json', "r") as file:
            bookings_data = json.load(file)
            result = []
            for booking in bookings_data.get("bookings", []):
                if str(booking.get("userid")) == str(userid):
                    for date_entry in booking.get("dates", []):
                        date_str = date_entry.get("date")
                        for movie_id in date_entry.get("movies", []):
                            result.append({
                                "userid": userid,
                                "movieId": movie_id,
                                "showtime": date_str
                            })
            return result
    
def movie_exists(_id):
    if USE_MONGO:
        movie = movies_collection.find_one({"id": _id})
        return movie is not None
    else:
        with open('./data/movies.json', "r") as file:
            movies = json.load(file)
            for movie in movies.get('movies', []):
                if movie['id'] == _id:
                    return True
    return False

            
def create_booking(_, info, userid, movieId, date):
    # Récupérer l'utilisateur courant
    requester_id = info.context.headers.get("X-User-Id")
    if not requester_id:
        raise Exception("Utilisateur non authentifié")

    # Vérifier droits
    user_response = requests.get(f"{USER_SERVICE_URL}/users/{requester_id}")
    if user_response.status_code != 200:
        raise Exception("Utilisateur courant introuvable")
    user = user_response.json()
    is_admin = user.get("admin", False)
    is_owner = str(requester_id) == str(userid)
    if not (is_admin or is_owner):
        raise Exception("Accès refusé : seuls les admins ou le propriétaire peuvent créer cette réservation")

    # Vérifier que le film existe (GraphQL)
    query = """
    query($id: String!) {
        movie_with_id(_id: $id) {
            id
        }
    }
    """
    variables = {"id": movieId}
    response = requests.post(
        MOVIE_SERVICE_URL,
        json={"query": query, "variables": variables},
        headers={"Content-Type": "application/json"}
    )
    movie_data = response.json()
    if not movie_data.get("data") or not movie_data["data"].get("movie_with_id"):
        raise Exception(f"Movie avec id {movieId} introuvable")

    # 🔹 Vérifier la disponibilité dans Schedule via gRPC
    if not is_movie_scheduled(date, movieId):
        raise Exception(f"Le film {movieId} n'est pas programmé le {date}")

    # Lecture du fichier bookings
    with open('./data/bookings.json', "r") as rfile:
        bookings_data = json.load(rfile)

    # Chercher le booking existant pour l'utilisateur
    user_booking = next((b for b in bookings_data.get("bookings", []) if b.get("userid") == userid), None)

    new_date_entry = {
        "date": date,
        "movies": [movieId]
    }

    if user_booking:
        user_booking["dates"].append(new_date_entry)
    else:
        new_booking = {
            "userid": userid,
            "dates": [new_date_entry]
        }
        bookings_data["bookings"].append(new_booking)
        user_booking = new_booking

    # Écriture du fichier
    if USE_MONGO:
        bookings_collection = db["bookings"]
        bookings_collection.update_one(
            {"userid": userid},
            {"$set": user_booking},
            upsert=True
        )
    else:
        with open('./data/bookings.json', "w") as wfile:
            json.dump(bookings_data, wfile, indent=2)

    return user_booking


def cancel_booking(_, info, userid, movieId, date):
    requester_id = info.context.headers.get("X-User-Id")
    if not requester_id:
        raise Exception("Utilisateur non authentifié")

    user_response = requests.get(f"{USER_SERVICE_URL}/users/{requester_id}")
    if user_response.status_code != 200:
        raise Exception("Utilisateur courant introuvable")
    user = user_response.json()

    is_admin = user.get("admin", False)
    is_owner = str(requester_id) == str(userid)

    if not (is_admin or is_owner):
        raise Exception("Accès refusé : seuls les admins ou le propriétaire peuvent annuler cette réservation")

    if USE_MONGO:
        bookings_collection = db["bookings"]
        user_booking = bookings_collection.find_one({"userid": userid})
        if not user_booking:
            raise Exception("Booking introuvable pour cet utilisateur")
    else:
        with open('./data/bookings.json', "r") as rfile:
            bookings_data = json.load(rfile)
        user_booking = next((b for b in bookings_data.get("bookings", []) if b.get("userid") == userid), None)
        if not user_booking:
            raise Exception("Booking introuvable pour cet utilisateur")

    for date_entry in user_booking["dates"]:
        if date_entry["date"] == date and movieId in date_entry["movies"]:
            date_entry["movies"].remove(movieId)

    user_booking["dates"] = [d for d in user_booking["dates"] if d["movies"]]

    if USE_MONGO:
        if not user_booking["dates"]:
            bookings_collection.delete_one({"userid": userid})
        else:
            bookings_collection.update_one({"userid": userid}, {"$set": user_booking}, upsert=True)
    else:
        bookings_data["bookings"] = [b for b in bookings_data["bookings"] if b["dates"]]
        with open('./data/bookings.json', "w") as wfile:
            json.dump(bookings_data, wfile, indent=2)

    return user_booking

