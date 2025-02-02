class LinkedInVerifierError(Exception):
    """Base exception for all application errors"""
    pass


class ValidationError(LinkedInVerifierError):
    """Input data validation errors"""
    pass


class APIError(LinkedInVerifierError):
    """Base class for API errors"""
    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


class ScrapinAPIError(APIError):
    """Specific Scrapin.io API errors"""
    pass


class BadRequestError(ScrapinAPIError):
    """400: The request was unacceptable, often due to missing a required parameter"""
    pass


class CredentialsError(ScrapinAPIError):
    """401: Invalid token provided in Authorization header"""
    pass


class PaymentRequiredError(ScrapinAPIError):
    """402: You don't have enough credits on your account to perform the request"""
    pass


class ForbiddenError(ScrapinAPIError):
    """403: The API key doesn't have permissions to perform the request"""
    pass


class ProfileNotFoundError(ScrapinAPIError):
    """404: The API didn't find any result for this query"""
    pass


class RateLimitError(ScrapinAPIError):
    """429: The request was unacceptable due to too many requests (500 requests per minute)"""
    pass


class ServerError(ScrapinAPIError):
    """500: The request fail due to a server error"""
    pass


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


class DatabaseError(Exception):
    """Database operation error"""
    pass