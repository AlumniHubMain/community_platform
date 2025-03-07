from fastapi import HTTPException

class LinkedInVerifierError(Exception):
    """Base exception for all application errors"""
    def __init__(self, message: str, status_code: int = 500):
        self.status_code = status_code
        super().__init__(message)


class ValidationError(LinkedInVerifierError):
    """Input data validation errors"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class APIError(LinkedInVerifierError):
    """Base class for API errors"""
    pass


class ScrapinAPIError(APIError):
    """Specific Scrapin.io API errors"""
    pass


class BadRequestError(ScrapinAPIError):
    """400: The request was unacceptable"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class CredentialsError(ScrapinAPIError):
    """401: Invalid token provided in Authorization header"""
    def __init__(self, message: str):
        super().__init__(message, status_code=401)


class PaymentRequiredError(ScrapinAPIError):
    """402: You don't have enough credits on your account to perform the request"""
    def __init__(self, message: str):
        super().__init__(message, status_code=402)


class ForbiddenError(ScrapinAPIError):
    """403: The API key doesn't have permissions to perform the request"""
    def __init__(self, message: str):
        super().__init__(message, status_code=403)


class ProfileNotFoundError(ScrapinAPIError):
    """404: The API didn't find any result for this query"""
    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class RateLimitError(ScrapinAPIError):
    """429: The request was unacceptable due to too many requests"""
    def __init__(self, message: str):
        super().__init__(message, status_code=429)


class ServerError(ScrapinAPIError):
    """500: The request fail due to a server error"""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class LinkedInError(Exception):
    """Base exception for LinkedIn errors"""
    pass


class LinkedInAuthError(LinkedInError):
    """LinkedIn authentication failed"""
    pass


class LinkedInBlockedError(LinkedInError):
    """LinkedIn blocked the request"""
    pass


class LinkedInSessionError(LinkedInError):
    """LinkedIn session expired"""
    pass


class TomQuirkAPIError(LinkedInError):
    """General TomQuirk API error"""
    pass


class DatabaseError(LinkedInVerifierError):
    """Database operation error"""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)