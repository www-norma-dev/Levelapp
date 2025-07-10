from abc import ABC, abstractmethod
from typing import Dict, Any
from pydantic import BaseModel

class BaseDatastore(ABC):

    @abstractmethod
    def fetch_document(self, user_id: str, collection_id: str, document_id: str, doc_type: str) -> BaseModel:
        """
        Retrieve and parse a document from the datastore based on its type.

        Args:
            user_id (str): ID of the user.
            collection_id (str): Name of the collection.
            document_id (str): ID of the document to retrieve.
            doc_type (str): Type of document (e.g., scenario, bundle).

        Returns:
            BaseModel: Parsed Pydantic model representing the document.
        """
        pass

    @abstractmethod
    def fetch_stored_results(self, user_id: str, collection_id: str, project_id: str, category_id: str, batch_id: str) -> Dict[str, Any]:
        """
        Retrieve stored batch results for a specific user and batch ID.

        Args:
            user_id (str): ID of the user.
            collection_id (str): Main collection name.
            project_id (str): Project identifier.
            category_id (str): Category/sub-collection name.
            batch_id (str): Batch identifier.

        Returns:
            Dict[str, Any]: Dictionary containing the stored result data.
        """
        pass

    @abstractmethod
    def save_batch_test_results(self, user_id: str, project_id: str, batch_id: str, data: Dict[str, Any]) -> None:
        """
        Store batch test results in the datastore for a specific user and batch.

        Args:
            user_id (str): ID of the user.
            project_id (str): Project identifier.
            batch_id (str): Batch identifier (used as document ID).
            data (Dict[str, Any]): Batch result data to store.
        """
        pass
