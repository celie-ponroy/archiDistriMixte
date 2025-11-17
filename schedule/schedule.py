import json
import grpc
from concurrent import futures
import schedule_pb2
import schedule_pb2_grpc

class MyScheduleServicer(schedule_pb2_grpc.ScheduleServicer):

    def __init__(self):
        with open('./data/schedule.json', 'r') as jsf:
            self.db = json.load(jsf)["schedule"]

    # ---------- GET ALL ----------
    def GetAllSchedules(self, request, context):
        schedules = [
            schedule_pb2.ScheduleData(
                date=s["date"],
                movies=s["movies"]
            )
            for s in self.db
        ]
        return schedule_pb2.Schedules(schedules=schedules)

    # ---------- GET BY DATE ----------
    def GetScheduleByDate(self, request, context):
        for s in self.db:
            if s["date"] == request.date:
                return schedule_pb2.ScheduleData(date=s["date"], movies=s["movies"])

        # Si pas trouvé : retourne vide
        return schedule_pb2.ScheduleData(date="", movies=[])
    
    # ---------- GET DATES BY MOVIE ----------
    def GetDatesByMovie(self, request, context):

        dates = []

        for s in self.db:
            if request.movie_id in s["movies"]:
                dates.append(s["date"])

        return schedule_pb2.DatesList(dates=dates)
    
    # ---------- CREATE ----------
    def CreateSchedule(self, request, context):
        # Vérifier si la date existe déjà
        for s in self.db:
            if s["date"] == request.date:
                # Ajouter uniquement le film s’il n’est pas déjà présent
                for movie in request.movies:
                    if movie not in s["movies"]:
                        s["movies"].append(movie)

                # Sauvegarde
                with open('./data/schedule.json', 'w') as jsf:
                    json.dump({"schedule": self.db}, jsf, indent=2)

                # Retourner l'entrée mise à jour
                return schedule_pb2.ScheduleData(
                    date=s["date"],
                    movies=s["movies"]
                )

        # Si la date n'existe pas, créer un nouvel horaire
        new_schedule = {"date": request.date, "movies": list(request.movies)}
        self.db.append(new_schedule)

        # Sauvegarde
        with open('./data/schedule.json', 'w') as jsf:
            json.dump({"schedule": self.db}, jsf, indent=2)

        return schedule_pb2.ScheduleData(
            date=request.date,
            movies=request.movies
        )

    # ---------- DELETE ----------
    def DeleteSchedule(self, request, context):
        initial_length = len(self.db)
        self.db = [s for s in self.db if s["date"] != request.date]

        if len(self.db) == initial_length:
            return schedule_pb2.DeleteResponse(success=False, message="Schedule not found")

        # Sauvegarde
        with open('./data/schedule.json', 'w') as jsf:
            json.dump({"schedule": self.db}, jsf, indent=2)

        return schedule_pb2.DeleteResponse(success=True, message="Schedule deleted")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    schedule_pb2_grpc.add_ScheduleServicer_to_server(MyScheduleServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
