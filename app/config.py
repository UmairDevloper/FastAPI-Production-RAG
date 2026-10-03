import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN")

    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_ENDPOINT = os.getenv("QDRANT_ENDPOINT")
    QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME")

    SIMULATE_FAILURE = os.getenv("SIMULATE_FAILURE")










settings = Settings()