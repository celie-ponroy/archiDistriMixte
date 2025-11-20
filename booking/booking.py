from ariadne import graphql_sync, make_executable_schema, load_schema_from_path, QueryType, MutationType
from flask import Flask, request, jsonify, make_response
import resolvers as r

PORT = 3001
HOST = '0.0.0.0'
app = Flask(__name__)

# Types GraphQL
query = QueryType()
mutation = MutationType()

# Association des resolvers
query.set_field("booking_with_id", r.booking_with_id)
mutation.set_field("create_booking", r.create_booking)
mutation.set_field("cancel_booking", r.cancel_booking)

# Chargement du schema GraphQL
type_defs = load_schema_from_path("booking.graphql")
schema = make_executable_schema(type_defs, query, mutation)

# Route d'accueil
@app.route("/", methods=['GET'])
def home():
    return make_response("<h1 style='color:blue'>Welcome to the Movie service!</h1>", 200)

# Endpoint GraphQL
@app.route("/graphql", methods=["POST"])
def graphql_server():
    data = request.get_json()
    success, result = graphql_sync(
        schema,
        data,
        context_value=request,
        debug=app.debug
    )
    return make_response(jsonify(result), 200 if success else 400)

if __name__ == "__main__":
    print(f"Server running on port {PORT}")
    app.run(host=HOST, port=PORT)