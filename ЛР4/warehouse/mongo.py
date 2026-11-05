from django.conf import settings
from pymongo import MongoClient

client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000, tz_aware=True)
db = client[settings.MONGO_DB]
telemetry = db["telemetry"]
