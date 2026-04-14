from pymongo import MongoClient
from config import MONGO_URI, MONGO_DATABASE, MONGO_COLLECTION_NOTES, MONGO_COLLECTION_LOGS


def get_mongo_client():
    return MongoClient(MONGO_URI)


def get_notes_collection():
    client = get_mongo_client()
    database = client[MONGO_DATABASE]
    return database[MONGO_COLLECTION_NOTES]


def get_logs_collection():
    client = get_mongo_client()
    database = client[MONGO_DATABASE]
    return database[MONGO_COLLECTION_LOGS]


def fetch_notes(limit=5):
    collection = get_notes_collection()
    return list(collection.find().limit(limit))


def search_notes(patient_ids, keyword=None):
    collection = get_notes_collection()

    if not patient_ids:
        return []

    query = {
        "patient_id": {"$in": patient_ids}
    }

    if keyword:
        query["note_text"] = {"$regex": keyword, "$options": "i"}

    return list(collection.find(query))


def log_query(log_data):
    collection = get_logs_collection()
    result = collection.insert_one(log_data)
    return str(result.inserted_id)