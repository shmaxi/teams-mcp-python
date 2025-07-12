"""Tests for OAuth2 providers."""

import pytest
from mcp_oauth2 import OAuth2Config, MicrosoftProvider, GoogleProvider, GenericOAuth2Provider


def test_microsoft_provider_initialization():
    """Test Microsoft provider initialization."""
    config = OAuth2Config(
        client_id="test-client-id",
        scopes=["User.Read"]
    )
    
    provider = MicrosoftProvider(config)
    
    assert provider.name == "microsoft"
    assert "login.microsoftonline.com" in provider.config.authorization_endpoint
    assert "login.microsoftonline.com" in provider.config.token_endpoint


def test_google_provider_initialization():
    """Test Google provider initialization."""
    config = OAuth2Config(
        client_id="test-client-id",
        client_secret="test-secret",
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    
    provider = GoogleProvider(config)
    
    assert provider.name == "google"
    assert "accounts.google.com" in provider.config.authorization_endpoint
    assert "oauth2.googleapis.com" in provider.config.token_endpoint


def test_generic_provider_initialization():
    """Test generic provider initialization."""
    config = OAuth2Config(
        client_id="test-client-id",
        client_secret="test-secret",
        authorization_endpoint="https://example.com/oauth/authorize",
        token_endpoint="https://example.com/oauth/token",
        scopes=["read", "write"]
    )
    
    provider = GenericOAuth2Provider("custom", config)
    
    assert provider.name == "custom"
    assert provider.config.authorization_endpoint == "https://example.com/oauth/authorize"
    assert provider.config.token_endpoint == "https://example.com/oauth/token"


def test_build_auth_url():
    """Test building authorization URL."""
    config = OAuth2Config(
        client_id="test-client-id",
        redirect_uri="http://localhost:3000/callback",
        scopes=["scope1", "scope2"],
        authorization_endpoint="https://example.com/authorize"
    )
    
    provider = GenericOAuth2Provider("test", config)
    url = provider.build_auth_url("test-state", "test-challenge")
    
    assert "https://example.com/authorize" in url
    assert "client_id=test-client-id" in url
    assert "state=test-state" in url
    assert "code_challenge=test-challenge" in url
    assert "code_challenge_method=S256" in url
    assert "scope=scope1+scope2" in url


def test_pkce_generation():
    """Test PKCE code verifier and challenge generation."""
    config = OAuth2Config(client_id="test")
    provider = GenericOAuth2Provider("test", config)
    
    verifier, challenge = provider.generate_pkce_pair()
    
    assert len(verifier) >= 43  # Base64 encoded 32 bytes
    assert len(challenge) >= 43  # Base64 encoded SHA256 hash
    assert verifier != challenge