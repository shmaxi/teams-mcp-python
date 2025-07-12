"""Microsoft/Azure AD OAuth2 provider."""

import httpx
from typing import Optional, Dict, Any

from ..base import OAuth2Provider, OAuth2Config, TokenResponse


class MicrosoftProvider(OAuth2Provider):
    """Microsoft/Azure AD OAuth2 provider."""
    
    def __init__(self, config: OAuth2Config, tenant_id: str = "common"):
        # Set Microsoft-specific endpoints
        config.authorization_endpoint = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"
        config.token_endpoint = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        super().__init__(config)
        self.tenant_id = tenant_id
    
    @property
    def name(self) -> str:
        return "microsoft"
    
    def build_auth_url(
        self,
        state: str,
        code_challenge: Optional[str] = None,
        additional_params: Optional[Dict[str, str]] = None
    ) -> str:
        """Build Microsoft auth URL with specific parameters."""
        params = additional_params or {}
        # Microsoft specific parameters
        params["response_mode"] = "query"
        params["prompt"] = "select_account"
        
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
        
        if self.config.scopes:
            data["scope"] = " ".join(self.config.scopes)
        
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
            
        if self.config.scopes:
            data["scope"] = " ".join(self.config.scopes)
        
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