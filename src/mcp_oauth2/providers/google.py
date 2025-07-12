"""Google OAuth2 provider."""

import httpx
from typing import Optional, Dict, Any

from ..base import OAuth2Provider, OAuth2Config, TokenResponse


class GoogleProvider(OAuth2Provider):
    """Google OAuth2 provider."""
    
    def __init__(self, config: OAuth2Config):
        # Set Google-specific endpoints
        config.authorization_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
        config.token_endpoint = "https://oauth2.googleapis.com/token"
        super().__init__(config)
    
    @property
    def name(self) -> str:
        return "google"
    
    def build_auth_url(
        self,
        state: str,
        code_challenge: Optional[str] = None,
        additional_params: Optional[Dict[str, str]] = None
    ) -> str:
        """Build Google auth URL with specific parameters."""
        params = additional_params or {}
        # Google specific parameters
        params["access_type"] = "offline"  # Request refresh token
        params["prompt"] = "consent"  # Force consent to get refresh token
        
        return super().build_auth_url(state, code_challenge, params)
    
    async def exchange_code(
        self,
        code: str,
        code_verifier: Optional[str] = None
    ) -> TokenResponse:
        """Exchange authorization code for tokens."""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.config.redirect_uri,
            "client_id": self.config.client_id,
        }
        
        if self.config.client_secret:
            data["client_secret"] = self.config.client_secret
        
        if code_verifier:
            data["code_verifier"] = code_verifier
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config.token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            
            token_data = response.json()
            return TokenResponse(
                access_token=token_data["access_token"],
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in"),
                refresh_token=token_data.get("refresh_token"),
                scope=token_data.get("scope")
            )
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token."""
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.config.client_id,
        }
        
        if self.config.client_secret:
            data["client_secret"] = self.config.client_secret
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config.token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            
            token_data = response.json()
            return TokenResponse(
                access_token=token_data["access_token"],
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in"),
                refresh_token=token_data.get("refresh_token", refresh_token),
                scope=token_data.get("scope")
            )