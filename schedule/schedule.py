import json
import grpc
from concurrent import futures
import os
import time
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import schedule_pb2
import schedule_pb2_grpc

def wait_for_mongo(client, max_retries=10, retry_interval=2):
    retries = 0
    while retries < max_retries:
        try:
            # Essayer une commande simple pour vérifier la connexion
            client.admin.command('ping')
            print("Connexion à MongoDB établie avec succès.")
            return True
        except ConnectionFailure:
            retries += 1
            print(f"MongoDB n'est pas encore prêt (essai {retries}/{max_retries}). Réessai dans {retry_interval} secondes...")
            time.sleep(retry_interval)
    print("Impossible de se connecter à MongoDB après plusieurs tentatives.")
    return False

class AppConfig:
    def __init__(self):
        self.USE_MONGO = os.getenv("USE_MONGO", "false").lower() == "true"
        self.MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017/archiDistriDB")

    @property
    def mongo_url(self):
        return self.MONGO_URL

config = AppConfig()

class MyScheduleServicer(schedule_pb2_grpc.ScheduleServicer):
    def __init__(self):
        if config.USE_MONGO:
            # Connexion à MongoDB avec authentification
            client = MongoClient(config.mongo_url)
            if not wait_for_mongo(client):
                raise ConnectionError("Impossible de se connecter à MongoDB.")

            db = client["archiDistriDB"]
            self.collection = db["schedules"]

            # Vérifie si la collection est vide et initialise-la si nécessaire
            if self.collection.count_documents({}) == 0:
                with open('./data/schedule.json', 'r') as jsf:
                    initial_data = json.load(jsf)["schedule"]
                    self.collection.insert_many(initial_data)
        else:
            # Utilisation des fichiers JSON
            with open('./data/schedule.json', 'r') as jsf:
                self.db = json.load(jsf)["schedule"]

    # Méthode pour sauvegarder les données dans le fichier JSON
    def _save_to_json(self):
        if not config.USE_MONGO:
            with open('./data/schedule.json', 'w') as jsf:
                json.dump({"schedule": self.db}, jsf, indent=2)

    # ---------- GET ALL ----------
    def GetAllSchedules(self, request, context):
        if config.USE_MONGO:
            schedules = list(self.collection.find({}))
            return schedule_pb2.Schedules(schedules=[
                schedule_pb2.ScheduleData(
                    date=s["date"],
                    movies=s["movies"]
                )
                for s in schedules
            ])
        else:
            return schedule_pb2.Schedules(schedules=[
                schedule_pb2.ScheduleData(
                    date=s["date"],
                    movies=s["movies"]
                )
                for s in self.db
            ])

    # ---------- GET BY DATE ----------
    def GetScheduleByDate(self, request, context):
        if config.USE_MONGO:
            schedule_data = self.collection.find_one({"date": request.date})
            if schedule_data:
                return schedule_pb2.ScheduleData(
                    date=schedule_data["date"],
                    movies=schedule_data["movies"]
                )
            return schedule_pb2.ScheduleData(date="", movies=[])
        else:
            for s in self.db:
                if s["date"] == request.date:
                    return schedule_pb2.ScheduleData(date=s["date"], movies=s["movies"])
            return schedule_pb2.ScheduleData(date="", movies=[])

    # ---------- GET DATES BY MOVIE ----------
    def GetDatesByMovie(self, request, context):
        dates = []
        if config.USE_MONGO:
            schedules = list(self.collection.find({"movies": request.movie_id}))
            dates = [s["date"] for s in schedules]
        else:
            for s in self.db:
                if request.movie_id in s["movies"]:
                    dates.append(s["date"])
        return schedule_pb2.DatesList(dates=dates)

    # ---------- CREATE ----------
    def CreateSchedule(self, request, context):
        if config.USE_MONGO:
            existing_schedule = self.collection.find_one({"date": request.date})
            if existing_schedule:
                # Ajouter les films qui ne sont pas déjà présents
                new_movies = [m for m in request.movies if m not in existing_schedule["movies"]]
                if new_movies:
                    self.collection.update_one(
                        {"date": request.date},
                        {"$push": {"movies": {"$each": new_movies}}}
                    )
                # Retourner l'entrée mise à jour
                updated_schedule = self.collection.find_one({"date": request.date})
                return schedule_pb2.ScheduleData(
                    date=updated_schedule["date"],
                    movies=updated_schedule["movies"]
                )
            else:
                # Créer un nouvel horaire
                new_schedule = {"date": request.date, "movies": list(request.movies)}
                self.collection.insert_one(new_schedule)
                return schedule_pb2.ScheduleData(
                    date=request.date,
                    movies=request.movies
                )
        else:
            # Rechercher si la date existe déjà
            for s in self.db:
                if s["date"] == request.date:
                    # Ajouter uniquement les films qui ne sont pas déjà présents
                    for movie in request.movies:
                        if movie not in s["movies"]:
                            s["movies"].append(movie)
                    self._save_to_json()
                    return schedule_pb2.ScheduleData(
                        date=s["date"],
                        movies=s["movies"]
                    )
            # Si la date n'existe pas, créer un nouvel horaire
            new_schedule = {"date": request.date, "movies": list(request.movies)}
            self.db.append(new_schedule)
            self._save_to_json()
            return schedule_pb2.ScheduleData(
                date=request.date,
                movies=request.movies
            )

    # ---------- DELETE ----------
    def DeleteSchedule(self, request, context):
        if config.USE_MONGO:
            result = self.collection.delete_one({"date": request.date})
            if result.deleted_count > 0:
                return schedule_pb2.DeleteResponse(success=True, message="Schedule deleted")
            return schedule_pb2.DeleteResponse(success=False, message="Schedule not found")
        else:
            initial_length = len(self.db)
            self.db = [s for s in self.db if s["date"] != request.date]
            if len(self.db) == initial_length:
                return schedule_pb2.DeleteResponse(success=False, message="Schedule not found")
            self._save_to_json()
            return schedule_pb2.DeleteResponse(success=True, message="Schedule deleted")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    schedule_pb2_grpc.add_ScheduleServicer_to_server(MyScheduleServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started on port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
