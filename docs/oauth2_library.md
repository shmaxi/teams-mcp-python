# MCP OAuth2 Library Documentation

The `mcp_oauth2` library provides a reusable implementation of OAuth2 authentication for MCP (Model Context Protocol) servers. It standardizes the OAuth2 flow into two MCP tools that can be used with any OAuth2 provider.

## Core Concepts

### OAuth2 Flow in MCP

The library implements OAuth2 as a stateless flow using two tools:

1. **`{provider}_is_authenticated`** - Check authentication status or initiate OAuth2 flow
2. **`{provider}_authorize`** - Complete OAuth2 flow by exchanging authorization code for tokens

This design allows MCP clients to handle OAuth2 authentication in a consistent way across different providers.

### PKCE Support

The library automatically uses PKCE (Proof Key for Code Exchange) when no client secret is provided, making it suitable for public clients like desktop applications or SPAs.

## Usage Guide

### Basic Setup

```python
from mcp_oauth2 import OAuth2Config, GenericOAuth2Provider, create_oauth2_tools
from mcp.server import Server

# 1. Configure OAuth2
config = OAuth2Config(
    client_id="your-client-id",
    client_secret="your-client-secret",  # Optional - omit for PKCE
    redirect_uri="http://localhost:3000/auth/callback",
    scopes=["scope1", "scope2"],
    authorization_endpoint="https://oauth.example.com/authorize",
    token_endpoint="https://oauth.example.com/token"
)

# 2. Create provider
provider = GenericOAuth2Provider("myservice", config)

# 3. Generate OAuth2 tools
oauth_tools = create_oauth2_tools(provider)

# 4. Add to your MCP server
server = Server("my-mcp-server")

@server.list_tools()
async def list_tools():
    return oauth_tools  # Returns is_authenticated and authorize tools
```

### Built-in Providers

#### Microsoft/Azure AD

```python
from mcp_oauth2 import MicrosoftProvider, OAuth2Config

config = OAuth2Config(
    client_id="your-azure-client-id",
    client_secret="optional-secret",
    scopes=["User.Read", "Mail.Read", "offline_access"]
)

# tenant_id can be "common", "organizations", "consumers", or specific tenant
provider = MicrosoftProvider(config, tenant_id="common")
```

#### Google

```python
from mcp_oauth2 import GoogleProvider, OAuth2Config

config = OAuth2Config(
    client_id="your-google-client-id",
    client_secret="your-google-client-secret",
    scopes=["https://www.googleapis.com/auth/drive.readonly"]
)

provider = GoogleProvider(config)
```

### Creating Custom Providers

For OAuth2 providers with special requirements, extend the base class:

```python
from mcp_oauth2 import OAuth2Provider, OAuth2Config, TokenResponse
import httpx

class GitHubProvider(OAuth2Provider):
    def __init__(self, config: OAuth2Config):
        config.authorization_endpoint = "https://github.com/login/oauth/authorize"
        config.token_endpoint = "https://github.com/login/oauth/access_token"
        super().__init__(config)
    
    @property
    def name(self) -> str:
        return "github"
    
    async def exchange_code(
        self, 
        code: str, 
        code_verifier: Optional[str] = None
    ) -> TokenResponse:
        # GitHub returns tokens in a different format
        data = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "code": code
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config.token_endpoint,
                data=data,
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            
            token_data = response.json()
            return TokenResponse(
                access_token=token_data["access_token"],
                token_type=token_data.get("token_type", "Bearer"),
                scope=token_data.get("scope")
            )
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        # GitHub doesn't support refresh tokens
        raise NotImplementedError("GitHub does not support refresh tokens")
```

## Authentication Flow

### Step 1: Check Authentication

The client first calls `{provider}_is_authenticated`:

```json
// Request
{
  "tool": "myservice_is_authenticated",
  "arguments": {
    "callback_url": "http://localhost:3000/auth/callback",
    "callback_state": {
      "user_id": "12345",
      "action": "list_files"
    }
  }
}

// Response (not authenticated)
{
  "authenticated": false,
  "auth_url": "https://oauth.example.com/authorize?client_id=...",
  "state": "random-state-value",
  "callback_state": { "user_id": "12345", "action": "list_files" }
}
```

### Step 2: User Authorization

The client opens the `auth_url` in a browser. After the user authorizes, they're redirected to:

```
http://localhost:3000/auth/callback?code=AUTH_CODE&state=random-state-value
```

### Step 3: Exchange Code

The client extracts the code and calls `{provider}_authorize`:

```json
// Request
{
  "tool": "myservice_authorize",
  "arguments": {
    "code": "AUTH_CODE",
    "callback_url": "http://localhost:3000/auth/callback?code=AUTH_CODE&state=random-state-value",
    "callback_state": { "user_id": "12345", "action": "list_files" }
  }
}

// Response (success)
{
  "success": true,
  "tokens": {
    "access_token": "eyJ...",
    "refresh_token": "...",
    "expires_in": 3600,
    "token_type": "Bearer"
  },
  "callback_state": { "user_id": "12345", "action": "list_files" }
}
```

### Step 4: Use Tokens

Pass tokens to your service-specific tools:

```json
{
  "tool": "myservice_list_files",
  "arguments": {
    "tokens": {
      "access_token": "eyJ...",
      "refresh_token": "..."
    }
  }
}
```

## Token Management

### Automatic Refresh

When tokens include a refresh token, the library can automatically refresh expired tokens:

```python
# In is_authenticated handler
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
```

### Token Validation

The library provides basic token validation:

```python
token = TokenResponse(
    access_token="...",
    expires_in=3600  # Automatically sets expires_at
)

if token.is_expired():
    # Token needs refresh
```

## Security Considerations

### PKCE for Public Clients

When no client secret is provided, the library automatically uses PKCE:

```python
# Public client (no secret)
config = OAuth2Config(
    client_id="your-client-id",
    # No client_secret - PKCE will be used
    scopes=["read", "write"]
)
```

### State Parameter

The library generates cryptographically secure state parameters to prevent CSRF attacks:

```python
state = secrets.token_urlsafe(32)  # Generated automatically
```

### Callback State

Use `callback_state` to maintain application state across the OAuth2 flow:

```python
# Before auth
callback_state = {
    "user_id": "12345",
    "return_to": "/dashboard",
    "action": "upload_file"
}

# After auth, callback_state is returned unchanged
```

## Error Handling

The library provides consistent error responses:

```json
// Token validation error
{
  "authenticated": false,
  "error": "Token validation failed",
  "message": "Token validation failed"
}

// Code exchange error
{
  "success": false,
  "error": "invalid_grant",
  "message": "Failed to exchange authorization code"
}
```

## Best Practices

1. **Always use HTTPS** in production for redirect URIs
2. **Store tokens securely** on the client side
3. **Implement token refresh** to avoid repeated authentication
4. **Use appropriate scopes** - request only what you need
5. **Handle errors gracefully** - provide clear messages to users

## Examples

See the `examples/` directory for complete implementations:
- `google_drive_mcp.py` - Google Drive integration
- `github_mcp.py` - GitHub integration
- Teams MCP server - Full implementation using Microsoft provider