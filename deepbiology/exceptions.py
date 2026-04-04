class DeepBiologyError(Exception):
    pass


class AuthenticationError(DeepBiologyError):
    pass


class InsufficientCreditsError(DeepBiologyError):
    pass


class NotFoundError(DeepBiologyError):
    pass