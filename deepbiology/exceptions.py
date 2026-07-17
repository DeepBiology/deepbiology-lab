class DeepBiologyError(Exception):
    pass


class AuthenticationError(DeepBiologyError):
    pass


class InsufficientCreditsError(DeepBiologyError):
    pass


class NotFoundError(DeepBiologyError):
    pass


class ResolutionError(DeepBiologyError):
    """Raised when a model catalog value cannot be resolved unambiguously."""


class ExternalServiceError(DeepBiologyError):
    """Raised when a supporting public data service cannot be queried."""
