"""
GovGuide AI — Service/Application Layer Exceptions
"""

class ServiceError(Exception):
    """Base exception for all service layer errors."""
    pass


class DuplicateUserError(ServiceError):
    """Raised when registering an email that already exists."""
    pass


class InvalidCredentialsError(ServiceError):
    """Raised when login password or email is incorrect."""
    pass


class InactiveUserError(ServiceError):
    """Raised when login is attempted on a deactivated account."""
    pass


class InvalidTokenError(ServiceError):
    """Raised when token parsing or validation fails."""
    pass


class UserNotFoundError(ServiceError):
    """Raised when a user is not found in the system."""
    pass


class SessionNotFoundError(ServiceError):
    """Raised when a query session is not found or not owned by the user."""
    pass
