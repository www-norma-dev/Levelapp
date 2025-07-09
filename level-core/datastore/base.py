from abc import ABC, abstractmethod
from typing import Dict, Any
from pydantic import BaseModel

class BaseDatastore(ABC):

    @abstractmethod
    def fetch_document(self, user_id: str, collection_id: str, document_id: str, doc_type: str) -> BaseModel:
        pass

    @abstractmethod
    def fetch_stored_results(self, user_id: str, collection_id: str, project_id: str, category_id: str, batch_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def store_extracted_data(self, user_id: str, document_id: str, data: Dict[str, Any], field_name: str) -> None:
        pass

    @abstractmethod
    def save_batch_test_results(self, user_id: str, project_id: str, batch_id: str, data: Dict[str, Any]) -> None:
        pass
