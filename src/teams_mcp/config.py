"""Configuration for Teams MCP server."""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class TeamsConfig(BaseSettings):
    """Teams MCP configuration."""
    
    # Azure AD App Registration
    azure_client_id: str = Field(...)
    azure_tenant_id: str = Field(default="common")
    azure_client_secret: Optional[str] = Field(default=None)
    
    # OAuth settings
    azure_redirect_uri: str = Field(default="http://localhost:3000/auth/callback")
    scopes: List[str] = Field(
        default_factory=lambda: [
            "Chat.ReadWrite",
            "ChatMessage.Send", 
            "User.Read",
            "offline_access"
        ]
    )
    
    # Server settings
    mcp_server_name: str = Field(default="teams-mcp")
    mcp_server_version: str = Field(default="0.2.1")
    
    # Debug
    debug: bool = Field(default=False)
    
    # Aliases for backward compatibility
    @property
    def redirect_uri(self) -> str:
        return self.azure_redirect_uri
    
    @property
    def server_name(self) -> str:
        return self.mcp_server_name
        
    @property
    def server_version(self) -> str:
        return self.mcp_server_version
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"