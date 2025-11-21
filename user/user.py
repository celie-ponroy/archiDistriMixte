from flask import Flask, request, jsonify, make_response
import json
import os
from pymongo import MongoClient

class AppConfig:
    def __init__(self):
        self.USE_MONGO = os.getenv("USE_MONGO", "false").lower() == "true"
        self.MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017/archiDistriDB")

    @property
    def mongo_url(self):
        return self.MONGO_URL

config = AppConfig()

# Connexion à MongoDB
if config.USE_MONGO:
    client = MongoClient(config.mongo_url)
    db = client["archiDistriDB"]
    users_collection = db["users"]
    if users_collection.count_documents({}) == 0:
        with open('./data/users.json', 'r') as jsf:
            initial_users = json.load(jsf)["users"]
            users_collection.insert_many(initial_users)
    users = list(users_collection.find({}))
else:
    with open('./data/users.json', "r") as jsf:
        users = json.load(jsf)["users"]

# Fonction pour écrire dans le fichier JSON
def write(users):
    if not config.USE_MONGO:
        with open('./data/users.json', 'w') as f:
            full = {"users": users}
            json.dump(full, f, indent=2)

app = Flask(__name__)
PORT = 3203
HOST = '0.0.0.0'

@app.route("/", methods=['GET'])
def home():
    return "<h1 style='color:blue'>Welcome to the User service!</h1>"

# Récupérer tous les utilisateurs
@app.route("/users", methods=['GET'])
def get_users():
   if config.USE_MONGO:
        users = list(users_collection.find({}))
        # Convertir les ObjectId en str pour la réponse JSON
        for user in users:
            user["_id"] = str(user["_id"])
   return make_response(jsonify(users), 200)

# Récupérer un utilisateur par son ID
@app.route("/users/<userid>", methods=['GET'])
def get_user_byid(userid):
    if config.USE_MONGO:
        user = users_collection.find_one({"id": userid})
        if user:
            user["_id"] = str(user["_id"])
            return make_response(jsonify(user), 200)
        return make_response(jsonify({"error": "User ID not found"}), 404)
    else:
        user = next((u for u in users if str(u["id"]) == str(userid)), None)
        if not user:
            return make_response(jsonify({"error": "User ID not found"}), 404)
        return make_response(jsonify(user), 200)

@app.route("/users/<userid>", methods=['POST'])
def add_user(userid):
    req = request.get_json()
    # Vérifier que l'ID n'existe pas déjà
    if config.USE_MONGO:
        if users_collection.find_one({"id": str(userid)}):
            return make_response(jsonify({"error": "User ID already exists"}), 400)
        # Ajouter le nouvel utilisateur
        result = users_collection.insert_one(req)
        req["_id"] = str(result.inserted_id)
        return make_response(jsonify(req), 200)
    else:
        if any(str(u["id"]) == str(userid) for u in users):
            return make_response(jsonify({"error": "User ID already exists"}), 400)
        # Ajouter le nouvel utilisateur
        users.append(req)
        write(users)
        return make_response(jsonify(req), 200)

# Supprimer un utilisateur (seul admin)
@app.route("/users/<userid>", methods=['DELETE'])
def delete_user(userid):
    req = request.get_json()
    requester_id = req.get("requester_id")
    if config.USE_MONGO:
        requester = users_collection.find_one({"id": requester_id})
        if not requester or (requester_id != userid and not requester.get("admin", False)):
            return make_response(jsonify({"error": "Only admin or the user itself can delete users"}), 403)
        user = users_collection.find_one({"id": userid})
        if not user:
            return make_response(jsonify({"error": "User ID not found"}), 404)
        users_collection.delete_one({"id": userid})
        return make_response(jsonify({"message": f"User ID {userid} deleted"}), 200)
    else:
        requester = next((u for u in users if str(u["id"]) == str(requester_id)), None)
        if not requester or (str(requester_id) != str(userid) and not requester.get("admin", False)):
            return make_response(jsonify({"error": "Only admin or the user itself can delete users"}), 403)
        user = next((u for u in users if str(u["id"]) == str(userid)), None)
        if not user:
            return make_response(jsonify({"error": "User ID not found"}), 404)
        users.remove(user)
        write(users)
        return make_response(jsonify({"message": f"User ID {userid} deleted"}), 200)

# Modifier un utilisateur (admin ou le user lui-même)
@app.route("/users/<userid>", methods=['PUT'])
def update_user(userid):
    req = request.get_json()
    requester_id = req.get("requester_id")
    if config.USE_MONGO:
        requester = users_collection.find_one({"id": str(requester_id)})
        if not requester or (str(requester_id) != str(userid) and not requester.get("admin", False)):
            return make_response(jsonify({"error": "Only admin or the user itself can update users"}), 403)
        user = users_collection.find_one({"id": str(userid)})
        if not user:
            return make_response(jsonify({"error": "User ID not found"}), 404)
        # Évite d’écraser requester_id ou id
        update_data = req.copy()
        update_data.pop("requester_id", None)
        update_data.pop("id", None)
        users_collection.update_one({"id": str(userid)}, {"$set": update_data})
        updated_user = users_collection.find_one({"id": str(userid)})
        updated_user["_id"] = str(updated_user["_id"])
        return make_response(jsonify(updated_user), 200)
    else:
        requester = next((u for u in users if str(u["id"]) == str(requester_id)), None)
        if not requester or (str(requester_id) != str(userid) and not requester.get("admin", False)):
            return make_response(jsonify({"error": "Only admin or the user itself can update users"}), 403)
        user = next((u for u in users if str(u["id"]) == str(userid)), None)
        if not user:
            return make_response(jsonify({"error": "User ID not found"}), 404)
        # Évite d’écraser requester_id ou id
        req.pop("requester_id", None)
        req.pop("id", None)
        user.update(req)
        write(users)
        return make_response(jsonify(user), 200)

if __name__ == "__main__":
    print(f"Server running on port {PORT}")
    app.run(host=HOST, port=PORT)
