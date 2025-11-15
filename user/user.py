from flask import Flask, request, jsonify, make_response
import json

app = Flask(__name__)

PORT = 3203
HOST = '0.0.0.0'

with open('{}/databases/users.json'.format("."), "r") as jsf:
   users = json.load(jsf)["users"]

def write(users):
   with open('{}/databases/users.json'.format("."), 'w') as f:
      full = {"users": users}
      json.dump(full, f, indent=2)

@app.route("/", methods=['GET'])
def home():
   return "<h1 style='color:blue'>Welcome to the User service!</h1>"

# Récupérer tous les utilisateurs
@app.route("/users", methods=['GET'])
def get_users():
   return make_response(jsonify(users), 200)

# Récupérer un utilisateur par son ID
@app.route("/users/<userid>", methods=['GET'])
def get_user_byid(userid):
   user = next((u for u in users if str(u["id"]) == str(userid)), None)
   if not user:
       return make_response(jsonify({"error": "User ID not found"}), 404)
   return make_response(jsonify(user), 200)

@app.route("/users/<userid>", methods=['POST'])
def add_user(userid):
    req = request.get_json()

    # Vérifier que l'ID n'existe pas déjà
    if any(str(u["id"]) == str(userid) for u in users):
        return make_response(jsonify({"error": "User ID already exists"}), 400)

    # Ajouter le user sans aucune vérification de rights
    users.append(req)
    write(users)
    return make_response(jsonify(req), 200)

# Supprimer un utilisateur (seul admin)
@app.route("/users/<userid>", methods=['DELETE'])
def delete_user(userid):
   req = request.get_json()
   requester_id = req.get("requester_id")
   requester = next((u for u in users if str(u["id"]) == str(requester_id)), None)

   if not requester or (str(requester_id) != str(userid) and not requester.get("admin", False)):
       return make_response(jsonify({"error":"Only admin or the user itself can delete users"}), 403)
   
   user = next((u for u in users if str(u["id"]) == str(userid)), None)
   if not user:
       return make_response(jsonify({"error":"User ID not found"}), 404)

   users.remove(user)
   write(users)
   return make_response(jsonify({"message":"User ID {} deleted".format(userid)}), 200)

# Modifier un utilisateur (admin ou le user lui-même)
@app.route("/users/<userid>", methods=['PUT'])
def update_user(userid):
   req = request.get_json()
   print(req)
   requester_id = req.get("requester_id")
   print(requester_id)
   requester = next((u for u in users if str(u["id"]) == str(requester_id)), None)
   print(requester)
   if not requester or (str(requester_id) != str(userid) and not requester.get("admin", False)):
       return make_response(jsonify({"error":"Only admin or the user itself can update users"}), 403)

   user = next((u for u in users if str(u["id"]) == str(userid)), None)
   if not user:
       return make_response(jsonify({"error":"User ID not found"}), 404)

   # Évite d’écraser requester_id ou id
   req.pop("requester_id", None)
   req.pop("id", None)
   user.update(req)
   write(users)
   return make_response(jsonify(user), 200)

if __name__ == "__main__":
   print("Server running in port %s"%(PORT))
   app.run(host=HOST, port=PORT)
