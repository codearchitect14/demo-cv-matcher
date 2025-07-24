class NotFoundException(Exception):
    """Raised when a resource is not found."""
    pass

class ValidationException(Exception):
    """Raised when validation fails."""
    pass
