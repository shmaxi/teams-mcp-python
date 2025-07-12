# Teams MCP Python

A Python implementation of Microsoft Teams MCP (Model Context Protocol) server with a **reusable OAuth2 authentication library** that can be used for building MCP servers for any OAuth2-based service.

## Features

### Reusable OAuth2 Library (`mcp_oauth2`)

- **Generic OAuth2 implementation** that works with any OAuth2 provider
- **Built-in providers** for Microsoft, Google, and generic OAuth2 services  
- **Standardized MCP tools** (`is_authenticated` and `authorize`) for OAuth2 flow
- **PKCE support** for public clients (no client secret required)
- **Automatic token refresh** handling
- **Easy to extend** for new OAuth2 providers

### Teams MCP Server

- **Full Microsoft Teams integration** via Graph API
- **Chat management**: List, create, and manage Teams chats
- **Messaging**: Send and retrieve messages
- **Rate limiting** with exponential backoff
- **Async/await** throughout for performance

## Installation

### Using uvx (Recommended)

The easiest way to use this MCP server is with [uvx](https://github.com/astral-sh/uv), which allows you to run Python applications without manual installation:

```bash
# Run the Teams MCP server directly
uvx teams-mcp-python

# Or specify with full package name
uvx --from teams-mcp-python teams-mcp
```

### Using pip

```bash
pip install teams-mcp-python
```

## Quick Start

### 1. Azure AD Setup

First, register an app in Azure Portal:

1. Go to Azure Portal > Azure Active Directory > App registrations
2. Click "New registration"
3. Set redirect URI to `http://localhost:3000/auth/callback` (Web platform)
4. Grant these API permissions (Delegated):
   - `Chat.ReadWrite`
   - `ChatMessage.Send`
   - `User.Read`
   - `offline_access`

### 2. Configuration

Create a `.env` file in your project:

```env
AZURE_CLIENT_ID=your-client-id
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_SECRET=your-client-secret  # Optional for public clients
AZURE_REDIRECT_URI=http://localhost:3000/auth/callback
DEBUG=true
```

### 3. Using with Claude Desktop

Add to your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

#### Option 1: Using uvx (Recommended)

```json
{
  "mcpServers": {
    "teams": {
      "command": "uvx",
      "args": ["teams-mcp-python"],
      "env": {
        "AZURE_CLIENT_ID": "your-client-id",
        "AZURE_TENANT_ID": "your-tenant-id",
        "AZURE_REDIRECT_URI": "http://localhost:3000/auth/callback"
      }
    }
  }
}
```

#### Option 2: Using Python

```json
{
  "mcpServers": {
    "teams": {
      "command": "python",
      "args": ["-m", "teams_mcp"],
      "env": {
        "AZURE_CLIENT_ID": "your-client-id",
        "AZURE_TENANT_ID": "your-tenant-id",
        "AZURE_REDIRECT_URI": "http://localhost:3000/auth/callback"
      }
    }
  }
}
```

#### Option 3: If installed globally

```json
{
  "mcpServers": {
    "teams": {
      "command": "teams-mcp",
      "env": {
        "AZURE_CLIENT_ID": "your-client-id",
        "AZURE_TENANT_ID": "your-tenant-id",
        "AZURE_REDIRECT_URI": "http://localhost:3000/auth/callback"
      }
    }
  }
}
```

### 4. Authentication Flow

When using the Teams MCP server in Claude:

1. **First use** - Claude will provide an authentication URL
2. **Open the URL** in your browser and sign in with your Microsoft account
3. **Copy the authorization code** from the redirect URL
4. **Provide the code** to Claude to complete authentication

Example conversation:
```
You: List my Teams chats

Claude: I'll help you list your Teams chats. First, I need to check your authentication status.

[Calls teams_is_authenticated]

You need to authenticate. Please visit this URL:
https://login.microsoftonline.com/common/oauth2/v2.0/authorize?...

After signing in, you'll be redirected to a URL with a code parameter. Please provide that code.

You: The URL shows: http://localhost:3000/auth/callback?code=ABC123...

Claude: [Calls teams_authorize with the code]

Great! I've successfully authenticated. Now let me list your chats.

[Calls teams_list_chats]

Here are your Teams chats:
1. Project Team - Group chat with 5 members
2. John Doe - One-on-one chat
...
```

## Available Tools

The Teams MCP server provides these tools:

### Authentication Tools
- `teams_is_authenticated` - Check authentication status or get auth URL
- `teams_authorize` - Complete OAuth2 flow with authorization code

### Teams Tools
- `teams_list_chats` - List all chats with optional filtering
- `teams_create_chat` - Create new one-on-one or group chats
- `teams_send_message` - Send messages to a chat
- `teams_get_messages` - Retrieve messages from a chat

## Creating Your Own OAuth2 MCP Server

The `mcp_oauth2` library makes it easy to create MCP servers for any OAuth2 service:

```python
from mcp_oauth2 import OAuth2Config, GenericOAuth2Provider, create_oauth2_tools
from mcp.server import Server

# Configure your OAuth2 provider
oauth_config = OAuth2Config(
    client_id="your-client-id",
    client_secret="your-client-secret",  # Optional for PKCE
    redirect_uri="http://localhost:3000/auth/callback",
    scopes=["scope1", "scope2"],
    authorization_endpoint="https://provider.com/oauth/authorize",
    token_endpoint="https://provider.com/oauth/token"
)

# Create provider instance
provider = GenericOAuth2Provider("myprovider", oauth_config)

# Get OAuth2 MCP tools
oauth_tools = create_oauth2_tools(provider)  # Creates is_authenticated and authorize tools

# Add to your MCP server
server = Server("my-mcp-server")

@server.list_tools()
async def list_tools():
    return oauth_tools + your_custom_tools
```

## OAuth2 Authentication Flow

The library implements a standard OAuth2 flow with two MCP tools:

### 1. `{provider}_is_authenticated`

Check if tokens are valid or generate an auth URL:

```json
// Request without tokens - generates auth URL
{
  "callback_url": "http://localhost:3000/auth/callback",
  "callback_state": { "custom": "data" }
}

// Response
{
  "authenticated": false,
  "auth_url": "https://provider.com/oauth/authorize?...",
  "state": "random-state-string"
}

// Request with tokens - validates them
{
  "tokens": {
    "access_token": "...",
    "refresh_token": "..."
  }
}

// Response
{
  "authenticated": true,
  "tokens": { /* refreshed tokens if needed */ }
}
```

### 2. `{provider}_authorize`

Exchange authorization code for tokens:

```json
// Request
{
  "code": "auth-code-from-callback",
  "callback_url": "http://localhost:3000/auth/callback?code=...&state=...",
  "callback_state": { "custom": "data" }
}

// Response
{
  "success": true,
  "tokens": {
    "access_token": "...",
    "refresh_token": "...",
    "expires_in": 3600
  }
}
```

## Built-in OAuth2 Providers

### Microsoft Provider

```python
from mcp_oauth2 import MicrosoftProvider, OAuth2Config

config = OAuth2Config(
    client_id="your-client-id",
    client_secret="your-secret",  # Optional
    scopes=["User.Read", "Mail.Read"]
)

provider = MicrosoftProvider(config, tenant_id="common")
```

### Google Provider

```python
from mcp_oauth2 import GoogleProvider, OAuth2Config

config = OAuth2Config(
    client_id="your-client-id",
    client_secret="your-secret",
    scopes=["https://www.googleapis.com/auth/drive.readonly"]
)

provider = GoogleProvider(config)
```

### Generic Provider

```python
from mcp_oauth2 import GenericOAuth2Provider, OAuth2Config

config = OAuth2Config(
    client_id="your-client-id",
    client_secret="your-secret",
    authorization_endpoint="https://example.com/oauth/authorize",
    token_endpoint="https://example.com/oauth/token",
    scopes=["read", "write"]
)

provider = GenericOAuth2Provider("custom", config)
```

## Creating a Custom OAuth2 Provider

Extend the base `OAuth2Provider` class:

```python
from mcp_oauth2 import OAuth2Provider, OAuth2Config, TokenResponse

class MyCustomProvider(OAuth2Provider):
    @property
    def name(self) -> str:
        return "mycustom"
    
    async def exchange_code(self, code: str, code_verifier: Optional[str] = None) -> TokenResponse:
        # Custom implementation
        pass
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        # Custom implementation
        pass
```

## Examples

See the `examples/` directory for complete implementations:

- `google_drive_mcp.py` - Google Drive MCP server
- `github_mcp.py` - GitHub MCP server

### Using Example Servers with Claude Desktop

You can run the example servers using uvx as well:

For the Google Drive example:

```json
{
  "mcpServers": {
    "google-drive": {
      "command": "uvx",
      "args": ["--from", "teams-mcp-python", "python", "-m", "examples.google_drive_mcp"],
      "env": {
        "GOOGLE_CLIENT_ID": "your-client-id",
        "GOOGLE_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

Or with a local installation:

```json
{
  "mcpServers": {
    "google-drive": {
      "command": "python",
      "args": ["/path/to/examples/google_drive_mcp.py"],
      "env": {
        "GOOGLE_CLIENT_ID": "your-client-id",
        "GOOGLE_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

For the GitHub example:

```json
{
  "mcpServers": {
    "github": {
      "command": "uvx",
      "args": ["--from", "teams-mcp-python", "python", "-m", "examples.github_mcp"],
      "env": {
        "GITHUB_CLIENT_ID": "your-client-id",
        "GITHUB_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```  

## Architecture

### OAuth2 Library Structure

```
mcp_oauth2/
├── base.py          # Base classes and interfaces
├── tools.py         # MCP tool creation
└── providers/       # OAuth2 provider implementations
    ├── generic.py   # Generic OAuth2 provider
    ├── microsoft.py # Microsoft-specific provider
    └── google.py    # Google-specific provider
```

### Teams MCP Structure

```
teams_mcp/
├── server.py        # Main MCP server
├── config.py        # Configuration
├── api/            # Teams API client
│   ├── client.py   # Graph API wrapper
│   └── rate_limiter.py
└── tools/          # Teams-specific MCP tools
    ├── list_chats.py
    ├── create_chat.py
    ├── send_message.py
    └── get_messages.py
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/shmaxi/teams-mcp-python.git
cd teams-mcp-python

# Install in development mode
pip install -e ".[dev]"
```

### Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=src

# Type checking
mypy src
```

### Code Quality

```bash
# Format code
black src tests

# Lint
ruff src tests
```

### Publishing

To publish a new version to PyPI:

```bash
# Build the package
python -m build

# Upload to PyPI (requires PyPI credentials)
python -m twine upload dist/*
```

After publishing, the package will be available via:
- `pip install teams-mcp-python`
- `uvx teams-mcp-python` (for direct execution without installation)

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.