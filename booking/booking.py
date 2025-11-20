from ariadne import graphql_sync, make_executable_schema, load_schema_from_path, QueryType, MutationType
from flask import Flask, request, jsonify, make_response
import os
import json
from pymongo import MongoClient

# Classe de configuration centralisée
class AppConfig:
    def __init__(self):
        self.USE_MONGO = os.getenv("USE_MONGO", "false").lower() == "true"
        self.USE_DOCKER = os.getenv("USE_DOCKER", "false").lower() == "true"
        self.MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/archiDistriDB")

    @property
    def mongo_url(self):
        return self.MONGO_URL

# Instanciation de la configuration
config = AppConfig()

# Connexion à MongoDB si nécessaire
if config.USE_MONGO:
    client = MongoClient(config.mongo_url)
    db = client["archiDistriDB"]
    bookings_collection = db["bookings"]

# Initialisation de Flask
PORT = 3001
HOST = '0.0.0.0'
app = Flask(__name__)

# Types GraphQL
query = QueryType()
mutation = MutationType()

# Résolveurs adaptés pour MongoDB ou JSON
def booking_with_id(_, info, _id):
    if config.USE_MONGO:
        booking = bookings_collection.find_one({"id": int(_id)})
        return booking
    else:
        with open('./data/bookings.json', "r") as file:
            bookings = json.load(file)
            for booking in bookings['bookings']:
                if booking['id'] == int(_id):
                    return booking
        return None

def create_booking(_, info, user_id, movie_id, schedule_id):
    new_booking = {
        "id": len(bookings_collection.find({})) + 1 if config.USE_MONGO else len(json.load(open('./data/bookings.json', "r"))['bookings']) + 1,
        "user_id": user_id,
        "movie_id": movie_id,
        "schedule_id": schedule_id,
        "status": "confirmed"
    }

    if config.USE_MONGO:
        bookings_collection.insert_one(new_booking)
        return new_booking
    else:
        with open('./data/bookings.json', "r") as file:
            bookings = json.load(file)
        bookings['bookings'].append(new_booking)
        with open('./data/bookings.json', "w") as file:
            json.dump(bookings, file)
        return new_booking

def cancel_booking(_, info, _id):
    if config.USE_MONGO:
        booking = bookings_collection.find_one({"id": int(_id)})
        if booking:
            bookings_collection.update_one(
                {"id": int(_id)},
                {"$set": {"status": "cancelled"}}
            )
            return bookings_collection.find_one({"id": int(_id)})
        return None
    else:
        with open('./data/bookings.json', "r") as file:
            bookings = json.load(file)
            for booking in bookings['bookings']:
                if booking['id'] == int(_id):
                    booking['status'] = "cancelled"
                    with open('./data/bookings.json', "w") as wfile:
                        json.dump(bookings, wfile)
                    return booking
        return None

# Association des résolveurs
query.set_field("booking_with_id", booking_with_id)
mutation.set_field("create_booking", create_booking)
mutation.set_field("cancel_booking", cancel_booking)

# Chargement du schéma GraphQL
type_defs = load_schema_from_path("booking.graphql")
schema = make_executable_schema(type_defs, query, mutation)

# Route d'accueil
@app.route("/", methods=['GET'])
def home():
    return make_response("<h1 style='color:blue'>Welcome to the Booking service!</h1>", 200)

# Endpoint GraphQL
@app.route("/graphql", methods=["POST"])
def graphql_server():
    data = request.get_json()
    success, result = graphql_sync(
        schema,
        data,
        context_value={"config": config},
        debug=app.debug
    )
    return make_response(jsonify(result), 200 if success else 400)

if __name__ == "__main__":
    print(f"Server running on port {PORT}")
    app.run(host=HOST, port=PORT)
