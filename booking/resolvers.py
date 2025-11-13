import json

import requests 

USER_SERVICE_URL = "http://localhost:3203" 
MOVIE_SERVICE_URL = "http://localhost:3002" 

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
            
def create_booking(_, info, userId, movieId, date):
    # Récupérer l'utilisateur courant
    requester_id = info.context.headers.get("X-User-Id")
    print(requester_id)
    if not requester_id:
        raise Exception("Utilisateur non authentifié")

    # Vérifier si l'utilisateur courant est admin ou propriétaire
    user_response = requests.get(f"{USER_SERVICE_URL}/users/{requester_id}")
    if user_response.status_code != 200:
        raise Exception("Utilisateur courant introuvable")
    user = user_response.json()

    is_admin = user.get("admin", False)
    is_owner = str(requester_id) == str(userId)

    if not (is_admin or is_owner):
        raise Exception("Accès refusé : seuls les admins ou le propriétaire peuvent créer cette réservation")

    # Vérifier que le movie existe via microservice Movie GraphQL
    query = """
    query ($id: ID!) {
      movie_with_id(id: $id) {
        id
        title
      }
    }
    """
    variables = {"id": movieId}
    response = requests.post(MOVIE_SERVICE_URL, json={"query": query, "variables": variables})
    movie_data = response.json()
    if not movie_data.get("data") or not movie_data["data"].get("movie_with_id"):
        raise Exception(f"Movie avec id {movieId} introuvable")

    # Lecture du fichier bookings
    with open('./data/bookings.json', "r") as rfile:
        bookings_data = json.load(rfile)

    # Chercher le booking existant pour l'utilisateur
    user_booking = next((b for b in bookings_data.get("bookings", []) if b.get("userid") == userId), None)

    new_date_entry = {
        "date": date,
        "movies": [movieId]
    }

    if user_booking:
        # Ajouter la nouvelle date
        user_booking["dates"].append(new_date_entry)
    else:
        # Créer un nouveau booking pour cet utilisateur
        new_booking = {
            "userid": userId,
            "dates": [new_date_entry]
        }
        bookings_data["bookings"].append(new_booking)
        user_booking = new_booking

    # Écriture du fichier
    with open('./data/bookings.json', "w") as wfile:
        json.dump(bookings_data, wfile, indent=2)

    return user_booking

def cancel_booking(_,info,_id):
    newbookings = {}
    canceledbooking = {}
    with open('{}/data/bookings.json'.format("."), "r") as rfile:
        bookings = json.load(rfile)
        for booking in bookings['bookings']:
            if booking['id'] == _id:
                canceledbooking = booking
                bookings['bookings'].remove(booking)
                newbookings = bookings
    with open('{}/data/bookings.json'.format("."), "w") as wfile:
        json.dump(newbookings, wfile)
    return canceledbooking

