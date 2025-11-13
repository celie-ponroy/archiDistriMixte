from flask import Flask, request, jsonify, make_response
import json
from werkzeug.exceptions import NotFound

app = Flask(__name__)

PORT = 3203
HOST = '0.0.0.0'

with open('{}/databases/users.json'.format("."), "r") as jsf:
   users = json.load(jsf)["users"]

def write(users):
   with open('{}/databases/users.json'.format("."), 'w') as f:
      full = {}
      full['users']=users
      json.dump(full, f)

@app.route("/", methods=['GET'])
def home():
   return "<h1 style='color:blue'>Welcome to the User service!</h1>"

# Récupérer tous les utilisateurs
@app.route("/users", methods=['GET'])
def get_users():
   res = make_response(jsonify(users), 200)
   return res

# Récupérer un utilisateur par son ID
@app.route("/users/<userid>", methods=['GET'])
def get_user_byid(userid):
   for user in users:
      if str(user["id"]) == str(userid):
         res = make_response(jsonify(user),200)
         return res
   return make_response(jsonify({"error":"User ID not found"}),500)

# Ajouter un utilisateur
@app.route("/users/<userid>", methods=['POST'])
def add_user(userid):
   req = request.get_json()

   for user in users:
      if str(user["id"]) == str(userid):
         print(user["id"])
         return make_response(jsonify({"error":"User ID already exists"}),500)

   users.append(req)
   write(users)
   res = make_response(jsonify(req),200)
   return res

# Supprimer un utilisateur (seul un admin peut le faire)
@app.route("/users/<userid>", methods=['DELETE'])
def delete_user(userid):
   req = request.get_json()
   requester_id = req.get("requester_id")
   # Vérifier si le requester est admin
   requester = next((u for u in users if str(u["id"]) == str(requester_id)), None)
   if not requester or not requester.get("admin", False):
      return make_response(jsonify({"error":"Only admin users can delete users"}),403)
   for user in users:
      if str(user["id"]) == str(userid):
         users.remove(user)
         write(users)
         return make_response(jsonify({"message":"User ID {} deleted".format(userid)}),200)
   return make_response(jsonify({"error":"User ID not found"}),500)

# Modifier un utilisateur (seul un admin peut le faire)
@app.route("/users/<userid>", methods=['PUT'])
def update_user(userid):
   req = request.get_json()

   requester_id = req.get("requester_id")
   # Vérifier si le requester est admin
   requester = next((u for u in users if str(u["id"]) == str(requester_id)), None)
   if not requester or not requester.get("admin", False):
      return make_response(jsonify({"error":"Only admin users can update users"}),403)
   for user in users:
      if str(user["id"]) == str(userid):
         user.update(req)
         write(users)
         return make_response(jsonify(user),200)
   return make_response(jsonify({"error":"User ID not found"}),500)

if __name__ == "__main__":
   print("Server running in port %s"%(PORT))
   app.run(host=HOST, port=PORT)
