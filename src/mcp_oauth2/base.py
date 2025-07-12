"""Base classes for OAuth2 MCP tools."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import secrets
import base64
import hashlib
from urllib.parse import urlencode, urlparse, parse_qs


@dataclass
class TokenResponse:
    """OAuth2 token response."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.expires_in and not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(seconds=self.expires_in)
    
    def is_expired(self) -> bool:
        """Check if token is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "refresh_token": self.refresh_token,
            "scope": self.scope,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


@dataclass
class OAuth2Config:
    """OAuth2 configuration."""
    client_id: str
    client_secret: Optional[str] = None
    redirect_uri: str = "http://localhost:3000/auth/callback"
    scopes: List[str] = None
    authorization_endpoint: str = ""
    token_endpoint: str = ""
    
    def __post_init__(self):
        if self.scopes is None:
            self.scopes = []


class OAuth2Provider(ABC):
    """Base OAuth2 provider for MCP tools."""
    
    def __init__(self, config: OAuth2Config):
        self.config = config
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
    
    def generate_pkce_pair(self) -> Tuple[str, str]:
        """Generate PKCE code verifier and challenge."""
        code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).decode('utf-8').rstrip('=')
        
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    def build_auth_url(
        self,
        state: str,
        code_challenge: Optional[str] = None,
        additional_params: Optional[Dict[str, str]] = None
    ) -> str:
        """Build authorization URL."""
        params = {
            "client_id": self.config.client_id,
            "response_type": "code",
            "redirect_uri": self.config.redirect_uri,
            "state": state,
        }
        
        if self.config.scopes:
            params["scope"] = " ".join(self.config.scopes)
        
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"
        
        if additional_params:
            params.update(additional_params)
        
        return f"{self.config.authorization_endpoint}?{urlencode(params)}"
    
    @abstractmethod
    async def exchange_code(
        self,
        code: str,
        code_verifier: Optional[str] = None
    ) -> TokenResponse:
        """Exchange authorization code for tokens."""
        pass
    
    @abstractmethod
    async def refresh_token(
        self,
        refresh_token: str
    ) -> TokenResponse:
        """Refresh access token."""
        pass
    
    def validate_callback_state(self, callback_url: str, expected_state: str) -> bool:
        """Validate OAuth callback state parameter."""
        parsed = urlparse(callback_url)
        params = parse_qs(parsed.query)
        return params.get('state', [None])[0] == expected_state