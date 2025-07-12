"""MCP tools for OAuth2 authentication."""

from typing import Dict, Any, Optional, List
import json
import secrets
from mcp.types import Tool
from .base import OAuth2Provider, TokenResponse


def create_oauth2_tools(provider: OAuth2Provider) -> List[Tool]:
    """Create is_authenticated and authorize MCP tools for an OAuth2 provider."""
    
    # Store PKCE verifiers keyed by state
    pkce_storage: Dict[str, str] = {}
    
    async def is_authenticated_handler(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check if tokens are valid or generate auth URL."""
        tokens = arguments.get("tokens", {})
        callback_url = arguments.get("callback_url")
        callback_state = arguments.get("callback_state", {})
        
        # If tokens provided, validate them
        if tokens and tokens.get("access_token"):
            try:
                # Check if refresh token exists and access token might be expired
                if tokens.get("refresh_token"):
                    # Try to refresh if we have a refresh token
                    # This is a simplified check - providers may have different validation
                    token_response = TokenResponse(
                        access_token=tokens["access_token"],
                        refresh_token=tokens.get("refresh_token"),
                        expires_at=tokens.get("expires_at")
                    )
                    
                    if token_response.is_expired() and token_response.refresh_token:
                        new_tokens = await provider.refresh_token(token_response.refresh_token)
                        return [{
                            "type": "text",
                            "text": json.dumps({
                                "authenticated": True,
                                "tokens": new_tokens.to_dict(),
                                "message": "Tokens refreshed successfully"
                            })
                        }]
                
                return [{
                    "type": "text", 
                    "text": json.dumps({
                        "authenticated": True,
                        "message": "Valid tokens provided"
                    })
                }]
            except Exception as e:
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "authenticated": False,
                        "error": str(e),
                        "message": "Token validation failed"
                    })
                }]
        
        # No tokens, generate auth URL
        if not callback_url:
            return [{
                "type": "text",
                "text": json.dumps({
                    "authenticated": False,
                    "error": "callback_url required when tokens not provided"
                })
            }]
        
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Generate PKCE if provider supports it
        auth_url = provider.build_auth_url(state)
        code_verifier = None
        
        if provider.config.client_secret is None:  # Public client, use PKCE
            code_verifier, code_challenge = provider.generate_pkce_pair()
            pkce_storage[state] = code_verifier
            auth_url = provider.build_auth_url(state, code_challenge)
        
        return [{
            "type": "text",
            "text": json.dumps({
                "authenticated": False,
                "auth_url": auth_url,
                "state": state,
                "callback_state": callback_state,
                "message": f"Visit the auth_url to authenticate with {provider.name}"
            })
        }]
    
    async def authorize_handler(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Exchange authorization code for tokens."""
        code = arguments.get("code")
        callback_url = arguments.get("callback_url")
        callback_state = arguments.get("callback_state", {})
        
        if not code or not callback_url:
            return [{
                "type": "text",
                "text": json.dumps({
                    "success": False,
                    "error": "code and callback_url are required"
                })
            }]
        
        try:
            # Extract state from callback URL for PKCE verification
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(callback_url)
            params = parse_qs(parsed.query)
            state = params.get('state', [None])[0]
            
            # Get PKCE verifier if we have one
            code_verifier = pkce_storage.pop(state, None) if state else None
            
            # Exchange code for tokens
            token_response = await provider.exchange_code(code, code_verifier)
            
            return [{
                "type": "text",
                "text": json.dumps({
                    "success": True,
                    "tokens": token_response.to_dict(),
                    "callback_state": callback_state,
                    "message": f"Successfully authenticated with {provider.name}"
                })
            }]
            
        except Exception as e:
            return [{
                "type": "text", 
                "text": json.dumps({
                    "success": False,
                    "error": str(e),
                    "message": "Failed to exchange authorization code"
                })
            }]
    
    # Create tool definitions
    is_authenticated_tool = Tool(
        name=f"{provider.name}_is_authenticated",
        description=f"Check if the provided tokens are valid for {provider.name}. If no tokens provided, generates auth URL.",
        inputSchema={
            "type": "object",
            "properties": {
                "tokens": {
                    "type": "object",
                    "description": "OAuth tokens (optional). If not provided, will generate auth URL",
                    "properties": {
                        "access_token": {"type": ["string", "null"]},
                        "refresh_token": {"type": ["string", "null"]},
                        "expires_at": {"type": ["string", "null"]}
                    }
                },
                "callback_url": {
                    "type": "string",
                    "description": "Callback URL for OAuth flow (required if tokens not provided)"
                },
                "callback_state": {
                    "type": "object",
                    "description": "State data to include in OAuth flow (optional)"
                }
            },
            "required": []
        }
    )
    
    authorize_tool = Tool(
        name=f"{provider.name}_authorize", 
        description=f"Exchange authorization code for {provider.name} tokens.",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Authorization code from OAuth callback"
                },
                "callback_url": {
                    "type": "string", 
                    "description": "Callback URL used in the authorization request"
                },
                "callback_state": {
                    "type": "object",
                    "description": "State data from OAuth callback (optional)"
                }
            },
            "required": ["code", "callback_url"]
        }
    )
    
    # Attach handlers
    setattr(is_authenticated_tool, 'handler', is_authenticated_handler)
    setattr(authorize_tool, 'handler', authorize_handler)
    
    return [is_authenticated_tool, authorize_tool]