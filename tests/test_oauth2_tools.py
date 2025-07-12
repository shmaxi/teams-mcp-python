"""Tests for OAuth2 MCP tools."""

import pytest
import json
from mcp_oauth2 import OAuth2Config, GenericOAuth2Provider, create_oauth2_tools


@pytest.mark.asyncio
async def test_is_authenticated_without_tokens():
    """Test is_authenticated tool without tokens."""
    config = OAuth2Config(
        client_id="test-client-id",
        authorization_endpoint="https://example.com/authorize",
        token_endpoint="https://example.com/token"
    )
    
    provider = GenericOAuth2Provider("test", config)
    tools = create_oauth2_tools(provider)
    
    # Find is_authenticated tool
    is_auth_tool = next(t for t in tools if t.name == "test_is_authenticated")
    handler = getattr(is_auth_tool, 'handler')
    
    # Call without tokens
    result = await handler({
        "callback_url": "http://localhost:3000/callback"
    })
    
    response = json.loads(result[0]["text"])
    
    assert response["authenticated"] is False
    assert "auth_url" in response
    assert "state" in response
    assert "https://example.com/authorize" in response["auth_url"]


@pytest.mark.asyncio
async def test_is_authenticated_with_valid_tokens():
    """Test is_authenticated tool with valid tokens."""
    config = OAuth2Config(
        client_id="test-client-id",
        authorization_endpoint="https://example.com/authorize",
        token_endpoint="https://example.com/token"
    )
    
    provider = GenericOAuth2Provider("test", config)
    tools = create_oauth2_tools(provider)
    
    # Find is_authenticated tool
    is_auth_tool = next(t for t in tools if t.name == "test_is_authenticated")
    handler = getattr(is_auth_tool, 'handler')
    
    # Call with tokens
    result = await handler({
        "tokens": {
            "access_token": "valid-token",
            "refresh_token": "refresh-token"
        }
    })
    
    response = json.loads(result[0]["text"])
    
    assert response["authenticated"] is True
    assert response["message"] == "Valid tokens provided"


@pytest.mark.asyncio
async def test_authorize_missing_params():
    """Test authorize tool with missing parameters."""
    config = OAuth2Config(
        client_id="test-client-id",
        authorization_endpoint="https://example.com/authorize",
        token_endpoint="https://example.com/token"
    )
    
    provider = GenericOAuth2Provider("test", config)
    tools = create_oauth2_tools(provider)
    
    # Find authorize tool
    auth_tool = next(t for t in tools if t.name == "test_authorize")
    handler = getattr(auth_tool, 'handler')
    
    # Call without required params
    result = await handler({})
    
    response = json.loads(result[0]["text"])
    
    assert response["success"] is False
    assert "error" in response
    assert "required" in response["error"]