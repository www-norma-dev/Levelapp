import json
import os
from typing import Dict, Any
from pydantic import BaseModel

from ..base import BaseDatastore
from ..firestore.schemas import ScenarioBatch, ExtractionBundle, DocType


class FileSystemService(BaseDatastore):
    """
    File-based datastore implementation.
    Instead of using Firestore or a remote database, this class reads and writes JSON files
    to/from a local folder, simulating a backend for testing or offline use cases.
    """

    def __init__(self, base_path: str = "data/"):
        """
        Initialize the FileSystemService with a base directory to read/write files.

        Args:
            base_path (str): Directory where all documents and results are stored.
        """
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True) 

    def _get_path(self, *parts) -> str:
        """
        Helper method to construct a full file path under the base directory.

        Args:
            *parts: Components of the file path (e.g., subfolders, filenames).

        Returns:
            str: The combined path.
        """
        return os.path.join(self.base_path, *parts)

    def fetch_document(
        self,
        user_id: str,
        collection_id: str,
        document_id: str,
        doc_type: DocType
    ) -> BaseModel:
        """
        Load a document (scenario or bundle) from disk and parse it as a Pydantic model.

        Args:
            user_id (str): ID of the user (currently unused in path).
            collection_id (str): ID of the collection (unused in this version).
            document_id (str): ID of the document (used as filename).
            doc_type (DocType): Type of document to parse (SCENARIO or BUNDLE).

        Returns:
            BaseModel: Parsed Pydantic model (ScenarioBatch or ExtractionBundle).

        Raises:
            ValueError: If the doc_type is unknown.
            FileNotFoundError: If the file does not exist.
        """
        path = self._get_path(user_id, collection_id, f"{document_id}.json")
        with open(path, "r") as f:
            data = json.load(f)

        # Return parsed model based on document type
        if doc_type == DocType.SCENARIO:
            return ScenarioBatch.model_validate(data)
        elif doc_type == DocType.BUNDLE:
            return ExtractionBundle.model_validate(data)
        else:
            raise ValueError(f"Unknown doc_type: {doc_type}")

    def fetch_stored_results(
        self,
        user_id: str,
        collection_id: str,
        project_id: str,
        category_id: str,
        batch_id: str
    ) -> Dict[str, Any]:
        """
        Load previously saved batch test results from disk.

        Args:
            user_id (str): ID of the user (currently unused).
            collection_id (str): ID of the collection (unused).
            project_id (str): ID of the project (unused).
            category_id (str): Category of the test (unused).
            batch_id (str): ID of the test batch (used in filename).

        Returns:
            Dict[str, Any]: Parsed JSON content from the file.

        Raises:
            FileNotFoundError: If the results file does not exist.
        """
        path = self._get_path(user_id, project_id, category_id, f"{batch_id}_results.json")

        try:
            with open(path, "r") as f:
                return json.load(f)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"[fetch_stored_results] File not found: {path}") from e



    def save_batch_test_results(
        self,
        user_id: str,
        project_id: str,
        batch_id: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Save batch test results to disk as a formatted JSON file.

        Args:
            user_id (str): ID of the user (currently unused).
            project_id (str): ID of the project (unused).
            batch_id (str): ID of the test batch (used in filename).
            data (Dict[str, Any]): Data to persist.

        Returns:
            None
        """
        path = self._get_path(user_id, project_id, "results", f"{batch_id}_results.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)  
