# config.py
import os
from dotenv import load_dotenv

class AppConfig:
    def __init__(self):
        load_dotenv()

        self.USE_MONGO = self._str_to_bool(os.getenv("USE_MONGO", "false"))
        self.USE_DOCKER = self._str_to_bool(os.getenv("USE_DOCKER", "false"))

        self.MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/archiDistriDB")
        self.DOCKER_MONGO_URL = os.getenv("DOCKER_MONGO_URL", "mongodb://mongo:27017/archiDistriDB")

        self.MOVIE_PORT = int(os.getenv("MOVIE_PORT", 3200))
        self.USER_PORT = int(os.getenv("USER_PORT", 3201))
        self.BOOKING_PORT = int(os.getenv("BOOKING_PORT", 3202))
        self.SCHEDULE_PORT = int(os.getenv("SCHEDULE_PORT", 50051))

    @staticmethod
    def _str_to_bool(value: str) -> bool:
        """Convertit une chaîne en booléen."""
        value = value.lower()
        if value in ("true", "1", "yes"):
            return True
        elif value in ("false", "0", "no"):
            return False
        else:
            raise ValueError(f"{value} n'est pas une valeur booléenne valide.")

    @property
    def mongo_url(self) -> str:
        """Retourne l'URL MongoDB appropriée selon l'environnement."""
        return self.DOCKER_MONGO_URL if self.USE_DOCKER else self.MONGO_URL

config = AppConfig()
