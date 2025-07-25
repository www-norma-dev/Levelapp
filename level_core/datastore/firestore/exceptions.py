class FirestoreServiceError(Exception):
    """Base class for Firestore service-related errors."""

    def __init__(self, message: str, *, cause: Exception = None):
        super().__init__(message)
        self.message = message
        self.cause = cause

    def __str__(self):
        base = f"FirestoreServiceError: {self.message}"
        if self.cause:
            return f"{base} (caused by {repr(self.cause)})"
        return base
