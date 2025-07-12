"""MCP OAuth2 - Reusable OAuth2 authentication tools for MCP servers."""

from .base import OAuth2Provider, OAuth2Config, TokenResponse
from .tools import create_oauth2_tools
from .providers import MicrosoftProvider, GoogleProvider, GenericOAuth2Provider

__version__ = "0.1.0"

__all__ = [
    "OAuth2Provider",
    "OAuth2Config", 
    "TokenResponse",
    "create_oauth2_tools",
    "MicrosoftProvider",
    "GoogleProvider",
    "GenericOAuth2Provider",
]