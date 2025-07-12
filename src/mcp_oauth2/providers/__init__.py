"""OAuth2 provider implementations."""

from .generic import GenericOAuth2Provider
from .microsoft import MicrosoftProvider
from .google import GoogleProvider

__all__ = [
    "GenericOAuth2Provider",
    "MicrosoftProvider", 
    "GoogleProvider",
]