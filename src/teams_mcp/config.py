"""Configuration for Teams MCP server."""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class TeamsConfig(BaseSettings):
    """Teams MCP configuration."""
    
    # Azure AD App Registration
    azure_client_id: str = Field(..., env="AZURE_CLIENT_ID")
    azure_tenant_id: str = Field("common", env="AZURE_TENANT_ID")
    azure_client_secret: Optional[str] = Field(None, env="AZURE_CLIENT_SECRET")
    
    # OAuth settings
    redirect_uri: str = Field("http://localhost:3000/auth/callback", env="AZURE_REDIRECT_URI")
    scopes: List[str] = Field(
        default_factory=lambda: [
            "Chat.ReadWrite",
            "ChatMessage.Send", 
            "User.Read",
            "offline_access"
        ]
    )
    
    # Server settings
    server_name: str = Field("teams-mcp", env="MCP_SERVER_NAME")
    server_version: str = Field("0.2.0", env="MCP_SERVER_VERSION")
    
    # Debug
    debug: bool = Field(False, env="DEBUG")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"