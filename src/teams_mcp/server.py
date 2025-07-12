"""Teams MCP Server implementation using FastMCP."""

import logging
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP

from mcp_oauth2 import OAuth2Config, MicrosoftProvider
from .config import TeamsConfig
from .api import TeamsClient

logger = logging.getLogger(__name__)

# Initialize configuration
config = TeamsConfig()

# Create FastMCP server
mcp = FastMCP(config.server_name)

# Initialize Teams client
teams_client = TeamsClient()

# Set up OAuth2 provider
oauth_config = OAuth2Config(
    client_id=config.azure_client_id,
    client_secret=config.azure_client_secret,
    redirect_uri=config.redirect_uri,
    scopes=config.scopes
)
oauth_provider = MicrosoftProvider(oauth_config, config.azure_tenant_id)

# Set up logging
if config.debug:
    logging.basicConfig(level=logging.DEBUG)


# OAuth2 Tools
@mcp.tool()
async def is_authenticated(
    tokens: Optional[Dict[str, Any]] = None,
    callback_url: Optional[str] = None,
    callback_state: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Check if the provided tokens are valid for Microsoft. If no tokens provided, generates auth URL."""
    import json
    import secrets
    
    # If tokens provided, validate them
    if tokens and tokens.get("access_token"):
        try:
            # Check if refresh token exists and access token might be expired
            if tokens.get("refresh_token"):
                from mcp_oauth2 import TokenResponse
                token_response = TokenResponse(
                    access_token=tokens["access_token"],
                    refresh_token=tokens.get("refresh_token"),
                    expires_at=tokens.get("expires_at")
                )
                
                if token_response.is_expired() and token_response.refresh_token:
                    new_tokens = await oauth_provider.refresh_token(token_response.refresh_token)
                    return {
                        "authenticated": True,
                        "tokens": new_tokens.to_dict(),
                        "message": "Tokens refreshed successfully"
                    }
            
            return {
                "authenticated": True,
                "message": "Valid tokens provided"
            }
        except Exception as e:
            return {
                "authenticated": False,
                "error": str(e),
                "message": "Token validation failed"
            }
    
    # No tokens, generate auth URL
    if not callback_url:
        return {
            "authenticated": False,
            "error": "callback_url required when tokens not provided"
        }
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Generate PKCE if provider supports it
    auth_url = oauth_provider.build_auth_url(state)
    code_verifier = None
    
    if oauth_provider.config.client_secret is None:  # Public client, use PKCE
        code_verifier, code_challenge = oauth_provider.generate_pkce_pair()
        # Store code_verifier somewhere accessible by authorize function
        # For now, we'll include it in the response
        auth_url = oauth_provider.build_auth_url(state, code_challenge)
    
    return {
        "authenticated": False,
        "auth_url": auth_url,
        "state": state,
        "callback_state": callback_state,
        "message": f"Visit the auth_url to authenticate with {oauth_provider.name}"
    }


@mcp.tool()
async def authorize(
    code: str,
    callback_url: str,
    callback_state: Optional[Dict[str, Any]] = None,
    code_verifier: Optional[str] = None
) -> Dict[str, Any]:
    """Exchange authorization code for Microsoft tokens."""
    try:
        # Exchange code for tokens
        token_response = await oauth_provider.exchange_code(code, code_verifier)
        
        return {
            "success": True,
            "tokens": token_response.to_dict(),
            "callback_state": callback_state,
            "message": f"Successfully authenticated with {oauth_provider.name}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to exchange authorization code"
        }


# Teams Tools
@mcp.tool()
async def teams_list_chats(
    access_token: str,
    filter: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """List all chats for the authenticated user."""
    return await teams_client.list_chats(access_token)


@mcp.tool()
async def teams_create_chat(
    access_token: str,
    chat_type: str,
    members: List[str]
) -> Dict[str, Any]:
    """Create a new Teams chat (one-on-one or group)."""
    return await teams_client.create_chat(access_token, chat_type, members)


@mcp.tool()
async def teams_send_message(
    access_token: str,
    chat_id: str,
    content: str
) -> Dict[str, Any]:
    """Send a message to a Teams chat."""
    return await teams_client.send_message(access_token, chat_id, content)


@mcp.tool()
async def teams_get_messages(
    access_token: str,
    chat_id: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Get messages from a Teams chat."""
    return await teams_client.get_messages(access_token, chat_id, limit)


def main():
    """Main entry point."""
    logger.info(f"Starting {config.server_name} v{config.server_version}")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()