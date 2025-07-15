from .firestore.service import FirestoreService
from .mongodb.service import MongoDBService
from .fss.service import FileSystemService

def get_datastore(backend: str = "firestore", **kwargs):
    """
    Factory method to return the correct datastore client.

    Args:
        backend (str): Name of the backend ("firestore", "mongodb", etc.)
        kwargs: Keyword arguments passed to the backend service constructor.

    Returns:
        An instance of a class that implements BaseDatastore.

    Raises:
        ValueError: If an unsupported backend is provided.
    """
    if backend == "firestore":
        return FirestoreService(**kwargs)

    elif backend == "mongodb":
        return MongoDBService(**kwargs)
    elif backend == "fss":
        return FileSystemService(**kwargs)


    raise ValueError(f"Unsupported backend: {backend}")
