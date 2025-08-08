from .config import (
    USERS_COLLECTION,
    PROJECTS_COLLECTION,
    EXTRACTION_COLLECTION,
    MULTIAGENT_COLLECTION,
)

from google.cloud.firestore_v1 import Client as FirestoreClient, DocumentReference

def get_document_path(client: FirestoreClient, user_id: str, collection_id: str, document_id: str) -> DocumentReference:
    return client.collection(USERS_COLLECTION).document(user_id).collection(collection_id).document(document_id)

def get_results_path(
    client: FirestoreClient, user_id: str, collection_id: str, document_id: str, sub_collection: str, sub_document_id: str
) -> DocumentReference:
    return (
        client.collection(USERS_COLLECTION)
        .document(user_id)
        .collection(collection_id)
        .document(document_id)
        .collection(sub_collection)
        .document(sub_document_id)
    )

def store_extracted_data_path(client: FirestoreClient, user_id: str, document_id: str) -> DocumentReference:
    return client.collection(USERS_COLLECTION).document(user_id).collection(EXTRACTION_COLLECTION).document(document_id)

def save_batch_results_path(client: FirestoreClient, user_id: str, project_id: str, batch_id: str) -> DocumentReference:
    return (
        client.collection(USERS_COLLECTION)
        .document(user_id)
        .collection(PROJECTS_COLLECTION)
        .document(project_id)
        .collection(MULTIAGENT_COLLECTION)
        .document(batch_id)
    )
