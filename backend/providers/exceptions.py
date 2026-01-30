"""Custom exceptions for LLM providers."""


class ProviderError(Exception):
    """Base exception for all provider errors."""
    pass


class RateLimitError(ProviderError):
    """Raised when rate limit is exceeded."""
    pass


class AuthenticationError(ProviderError):
    """Raised when authentication fails."""
    pass


class InvalidRequestError(ProviderError):
    """Raised when the request is invalid."""
    pass
