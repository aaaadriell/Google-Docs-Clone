# Base Class for Authentication Exceptions
class AuthError(Exception):
    """Base class for authentication-related exceptions."""

####################################################
# For JWT Access Token Validity Exceptions
####################################################
class InvalidJWTTokenError(AuthError):
    """Access token is malformed, tampered with, or not an access token."""


class ExpiredJWTTokenError(AuthError):
    """Access token was valid but has expired. The client should call /refresh."""

####################################################
# For Refresh Token Validity Exceptions
####################################################
class InvalidRefreshTokenError(AuthError):
    """Refresh Token is missing, malformed, tarmpered with, expired or not a refresh token."""