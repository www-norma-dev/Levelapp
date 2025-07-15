from ..base import BaseDatastore
from pydantic import BaseModel
from typing import Dict, Any

class MongoDBService(BaseDatastore):
    """
    Stub implementation of a MongoDB-based datastore.
    This is just a placeholder to support future MongoDB integration.
    """

    def __init__(self, client):
        """
        Set up the MongoDB service with a client instance.

        Args:
            client: MongoDB client (e.g., pymongo.MongoClient).
        """
        self.client = client

    def fetch_document(self, user_id: str, collection_id: str, document_id: str, doc_type: str) -> BaseModel:
        """
        Fetch a document from the database.
        Not yet implemented — just here to define the interface.

        Args:
            user_id: ID of the user.
            collection_id: Collection or dataset name.
            document_id: Unique identifier for the document.
            doc_type: Expected type of document (e.g., 'scenario').

        Raises:
            NotImplementedError
        """
        raise NotImplementedError("MongoDB backend is not implemented yet.")

    def fetch_stored_results(self, user_id: str, collection_id: str, project_id: str, category_id: str, batch_id: str) -> Dict[str, Any]:
        """
        Retrieve stored results for a batch run (like metrics or predictions).
        Currently just a placeholder.

        Args:
            user_id: ID of the user.
            collection_id: Collection where data is grouped.
            project_id: ID of the related project.
            category_id: Result category or tag.
            batch_id: Batch ID to fetch.

        Raises:
            NotImplementedError
        """
        raise NotImplementedError("MongoDB backend is not implemented yet.")

    def save_batch_test_results(self, user_id: str, project_id: str, batch_id: str, data: Dict[str, Any]) -> None:
        """
        Save test results for a given batch.
        Placeholder — not writing anything yet.

        Args:
            user_id: Who owns the data.
            project_id: Project reference.
            batch_id: ID of the test batch.
            data: Results to save.

        Raises:
            NotImplementedError
        """
        raise NotImplementedError("MongoDB backend is not implemented yet.")
