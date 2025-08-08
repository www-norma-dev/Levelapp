"""
'firestore/service.py': FirestoreService handles interactions with Firestore to fetch and parse scenario data.
"""
import logging
from typing import List, Dict, Any, Type

from google.cloud import storage
from google.cloud.firestore_v1 import DocumentReference, DocumentSnapshot, SERVER_TIMESTAMP

from pydantic import ValidationError, BaseModel
from werkzeug.exceptions import InternalServerError, ServiceUnavailable, HTTPException
from google.api_core.exceptions import GoogleAPIError, NotFound

from .schemas import ScenarioBatch, ExtractionBundle, DocType

from .config import DEFAULT_SCENARIO_FIELD  
from .paths import get_document_path, get_results_path, store_extracted_data_path, save_batch_results_path  
from ..base import BaseDatastore
from .exceptions import FirestoreServiceError
from google.cloud import firestore


ERROR_MESSAGES = {
    "document_not_found": "Document not found.",
    "gcs_service_unavailable": "Google cloud service unavailable.",
    "doc_not_found": "Document not found in Firestore.",
    "invalid_format": "Invalid model format",
    "invalid_input": "Invalid inputs",
    "unexpected_error": "Unexpected error",
}

logger = logging.getLogger("batch-test")


class FirestoreService(BaseDatastore):
    def __init__(self, credentials_path: str = None):
        """
        Args:
            credentials_path (str): Path to service account JSON key file.
        """
        if credentials_path:
            self._firestore_client = firestore.Client.from_service_account_json(credentials_path)
        else:
            self._firestore_client = firestore.Client()

        self._storage_client = storage.Client()

        from google.auth import default
        creds, project = default()


    @staticmethod
    def parser(doc: DocumentSnapshot, model: Type[BaseModel]) -> BaseModel:
        """
        Parse a Firestore document into a validated Pydantic model.

        Args:
            doc (DocumentSnapshot): Firestore document snapshot to be parsed.
            model (Type[BaseModel]): Pydantic model class to validate and structure the data.

        Returns:
            BaseModel: An instance of the provided model populated with the document's data.

        Raises:
            ValueError: If the Firestore document is empty or missing.
            InternalServerError: If the data fails validation against the model.
        """
        data = doc.to_dict()
        if not data:
            raise ValueError("[_parser] Missig document data")

        try:
            logger.info("[_parser] Parsing parsing data...")
            return model.model_validate(data)

        except ValidationError as e:
            logger.error(f"[_parse_scenarios] Failed to parse Firestore document: {e.errors()}")
            raise InternalServerError(description=ERROR_MESSAGES["invalid_format"])



    def list_storage_buckets(self) -> List[str]:
        """
        List all Google Cloud Storage buckets associated with the project.

        Returns:
            List[str]: List of bucket names.

        Raises:
            HTTPException: If there is a Google API error or permission issue.
        """
        try:
            logger.info("[list_storage_buckets] Fetching storage buckets for project")
            buckets = self._storage_client.list_buckets()
            bucket_names = [bucket.name for bucket in buckets]
            logger.info(f"[list_storage_buckets] Found {len(bucket_names)} buckets")
            return bucket_names

        except GoogleAPIError as e:
            logger.error(f"[list_storage_buckets] Google API error: {e}")
            raise ServiceUnavailable(description=ERROR_MESSAGES["gcs_service_unavailable"])

        except Exception as e:
            logger.error(f"[list_storage_buckets] Unexpected error: {e}")
            raise InternalServerError(description=ERROR_MESSAGES["unexpected_error"])

    def retrieve_pdf_files(self, bucket_name: str, folder: str = "") -> List[storage.Blob]:
        """
        Retrieve PDF files from a specific bucket and specified folder.

        Args:
            bucket_name (str): Name of the bucket.
            folder (str): Name of the folder.

        Returns:
            List[storage.Blob]: List of Blob objects.

        Raises:
            ServiceUnavailable: If there is a Google API error or permission issue.
            HTTPException: if blob list retrieval fails unexpectedly.

        """
        try:
            if bucket_name not in self.list_storage_buckets():
                logger.warning(f"[set_default_bucket] No bucket found with the name: {bucket_name}")
                return []

            bucket = self._storage_client.get_bucket(bucket_or_name=bucket_name)
            files = list(bucket.list_blobs(prefix=folder, match_glob='**.pdf'))
            return files

        except NotFound:
            logger.error(f"[retrieve_pdf_files] No files found in folder: {folder}")
            raise

        except GoogleAPIError as e:
            logger.error(f"[retrieve_pdf_files] Google API error: {e}")
            raise ServiceUnavailable(description=ERROR_MESSAGES["gcs_service_unavailable"])

        except Exception as e:
            logger.error(f"[retrieve_pdf_files] Unexpected error: {e}")
            raise InternalServerError(description=ERROR_MESSAGES["unexpected_error"])

    def transfer_files(
            self,
            source_bucket: str,
            source_blob: str,
            destination_bucket: str,
            destination_blob: str
    ):
        """
        Transfer an object from one Google Cloud Storage bucket to another.

        Args:
            source_bucket (str): Name of the source bucket.
            source_blob (str): Path to the source object in the source bucket.
            destination_bucket (str): Name of the destination bucket.
            destination_blob (str): Path to store the object in the destination bucket.

        Return:
            bool : Flag that indicates whether the operation was successful or not.

        Raises:
            ServiceUnavailable: If GCS storage service is unavailable.
            HTTPException: If transfer operation fails unexpectedly.
        """
        if not all([source_bucket.strip(), source_blob.strip(), destination_bucket.strip(), destination_blob.strip()]):
            raise ValueError("Invalid input parameters")

        try:
            logger.info(
                f"[transfer_files] Transferring {source_blob} from "
                f"{source_bucket} to {destination_blob} in {destination_bucket}"
            )

            source_bucket = self._storage_client.get_bucket(source_bucket)
            source_blob = source_bucket.get_blob(blob_name=source_blob)
            if not source_blob:
                logger.warning(f"[transfer_files] Source object {source_blob} not found in {source_bucket}")
                raise HTTPException(description="Source object not found")

            destination_bucket = self._storage_client.get_bucket(destination_bucket)

            blob_copy = source_bucket.copy_blob(
                blob=source_blob,
                destination_bucket=destination_bucket,
                new_name=destination_blob,
            )

            if not blob_copy.exists():
                logger.error(
                    f"[transfer_files] Copy operation failed: "
                    f"{destination_blob} does not exist in {destination_bucket}"
                )
                raise HTTPException(description="Copy operation failed")

            return True

        except GoogleAPIError as e:
            logger.error(f"[transfer_files] Google API error: {e}")
            raise ServiceUnavailable(description=ERROR_MESSAGES["gcs_service_unavailable"])

        except Exception as e:
            logger.error(f"[transfer_files] Unexpected error: {e}")
            raise InternalServerError(description=ERROR_MESSAGES["unexpected_error"])

    def _fetch_document(self, user_id: str, collection_id: str, document_id: str):
        """
        Fetch a document from a specific collection in Firestore.

        Args:
            user_id (str): User ID.
            collection_id (str): Collection ID.
            document_id (str): Document ID.

        Returns:
            Document (DocumentSnapshot): a snapshot of the document.

        Raises:
            ServiceUnavailable: If GCS storage service is unavailable.
            HTTPException: If transfer operation fails unexpectedly.
        """
        if not all([user_id.strip(), collection_id.strip(), document_id.strip()]):
            raise ValueError("Invalid input parameters")

        try:
            doc_ref = get_document_path(self._firestore_client,user_id=user_id, collection_id=collection_id, document_id=document_id)
            doc = doc_ref.get()

            if not doc.exists:
                logger.warning(f"[fetch_document] Document {document_id} not found.")
                raise NotFound(message=ERROR_MESSAGES["document_not_found"])

            return doc

        except GoogleAPIError as e:
            logger.error(f"[_fetch_document] Firestore API error: {e}")
            raise FirestoreServiceError(ERROR_MESSAGES["gcs_service_unavailable"], cause=e)

        except Exception as e:
            logger.error(f"[_fetch_document] Unexpected error while fetching document <ID:{document_id}>: {e}")
            raise FirestoreServiceError(ERROR_MESSAGES["unexpected_error"], cause=e)

    def fetch_document(
            self,
            user_id: str,
            collection_id: str,
            document_id: str,
            doc_type: DocType.SCENARIO
    ) -> BaseModel:
        """
        Fetch scenario/bundle document for a specific user, collection, and scenario ID.

        Args:
            user_id (str): User ID.
            collection_id (str): Collection ID.
            document_id (str): Scenario ID.
            doc_type (str): Document type.

        Returns:
            ScenarioBatch: Parsed scenario batch.

        Raises:
            ServiceUnavailable: If GCS storage service is unavailable.
            HTTPException: If transfer operation fails unexpectedly.
        """
        try:
            logger.info(f"[fetch_document] Fetching scenarios for user {user_id}")
            doc = self._fetch_document(user_id=user_id, collection_id=collection_id, document_id=document_id)

            if doc_type == DocType.SCENARIO:
                return self.parser(doc=doc, model=ScenarioBatch)

            elif doc_type == DocType.BUNDLE:
                return self.parser(doc=doc, model=ExtractionBundle)

            else:
                logger.error(f"[fetch_document] Unexpected document type {doc_type}")
                raise FirestoreServiceError(ERROR_MESSAGES["invalid_format"], cause=E)

        except NotFound:
            logger.warning(f"[fetch_document] Document not found: {document_id}")
            raise NotFound(message=ERROR_MESSAGES["document_not_found"])

        except GoogleAPIError as e:
            logger.error(f"[fetch_document] Firestore API error: {e}")
            raise FirestoreServiceError(ERROR_MESSAGES["gcs_service_unavailable"], cause=e)

        except Exception as e:
            logger.error(f"[fetch_document] Unexpected error: {e}")
            raise FirestoreServiceError(ERROR_MESSAGES["unexpected_error"], cause=e)

    def fetch_stored_results(self, user_id: str, collection_id: str, project_id: str, category_id: str, batch_id: str):
        """
        Fetch stored batch test results for a specific, user, collection, and batch ID.

        Args:
            user_id (str): User ID.
            collection_id (str): Collection ID.
            project_id (str): Project ID.
            category_id (str): Category (e.g., 'batchTestMultiAgent').
            batch_id (str): Batch ID.

        Returns:
            Dict[str, Any]: Firestore document snapshot.

        Raises:
            Serv
            HTTPException: If the scenario is not found or if there is a Firestore API error.
        """
        try:
            logger.info(f"[fetch_stored_results] Fetching stored results for batch ID: {batch_id}")
            doc_ref = get_results_path(
                self._firestore_client,
                user_id=user_id,
                collection_id=collection_id,
                project_id=project_id,
                category_id=category_id,
                batch_id=batch_id
            )
            doc = doc_ref.get()

            if not doc.exists:
                logger.warning(f"[fetch_stored_results] Batch test results not found: user={user_id}, batch={batch_id}")
                raise NotFound(message=ERROR_MESSAGES["doc_not_found"])

            return doc.to_dict()

        except GoogleAPIError as e:
            logger.error(f"[fetch_stored_results] Firestore API error: {e}")
            raise ServiceUnavailable(description=ERROR_MESSAGES["gcs_service_unavailable"])

        except Exception as e:
            logger.error(f"[fetch_stored_results] Unexpected error: {e}")
            raise InternalServerError(description=ERROR_MESSAGES["unexpected_error"])

    def store_extracted_data(
            self,
            user_id: str,
            document_id: str,
            data: Dict[str, Any],
            field_name: str = DEFAULT_SCENARIO_FIELD
    ) -> None:
        """
        Persist extracted data into Firestore under:
        users/{userId}/projects/{projectId}/dataExtraction/{batchId}

        Args:
            user_id (str): ID of the user.
            document_id (str): ID of the document (bundle).
            data (Dict[str, Any]): Extracted data.
            field_name (str): Name of the key under which the data will be stored.
        """
        wrapped_data = {
            field_name: data,
            "updatedAt": SERVER_TIMESTAMP
        }

        doc_ref = store_extracted_data_path(self._firestore_client, user_id, document_id)

        try:
            doc_ref.set(wrapped_data, merge=True)
            logger.info(f"[store_extracted_data] Storing extracted data under ID: {document_id}")

        except GoogleAPIError as e:
            logger.error(f"[save_batch_test_results] Firestore API error: {e}")
            raise ServiceUnavailable(description=ERROR_MESSAGES["gcs_service_unavailable"])

        except Exception as e:
            logger.error(f"[save_batch_test_results] Unexpected error: {e}")
            raise InternalServerError(description=ERROR_MESSAGES["gcs_service_unavailable"])

    def save_batch_test_results(
            self,
            user_id: str,
            project_id: str,
            batch_id: str,
            data: Dict[str, Any],
    ) -> None:
        """
        Persist batch test result to Firestore under:
        users/{userId}/projects/{projectId}/batchTestMultiAgent/{batchId}

        Args:
            user_id (str): ID of the user.
            project_id (str): ID of the project.
            batch_id (str): ID of the batch (used as the document ID).
            data (Dict[str, Any]): Batch simulation result data.
        """
        doc_data = dict(data)
        doc_data["updatedAt"] = SERVER_TIMESTAMP

        doc_ref = save_batch_results_path(self._firestore_client, user_id, project_id, batch_id)

        try:
            doc_ref.set(doc_data, merge=True)
            logger.info(
                f"[save_batch_test_results] Merged data into batchId: {batch_id}"
            )

        except GoogleAPIError as e:
            logger.error(f"[save_batch_test_results] Firestore API error: {e}")
            raise ServiceUnavailable(description=ERROR_MESSAGES["gcs_service_unavailable"])

        except Exception as e:
            logger.error(f"[save_batch_test_results] Unexpected error: {e}")
            raise InternalServerError(description=ERROR_MESSAGES["gcs_service_unavailable"])