"""Teams MCP Server implementation."""

import logging
import asyncio
from typing import List
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

from mcp_oauth2 import OAuth2Config, MicrosoftProvider, create_oauth2_tools
from .config import TeamsConfig
from .api import TeamsClient
from .tools import (
    create_list_chats_tool,
    create_create_chat_tool,
    create_send_message_tool,
    create_get_messages_tool
)

logger = logging.getLogger(__name__)


class TeamsServer:
    """Teams MCP Server."""
    
    def __init__(self, config: TeamsConfig):
        self.config = config
        self.server = Server(self.config.server_name)
        self.teams_client = TeamsClient()
        
        # Set up OAuth2 provider
        oauth_config = OAuth2Config(
            client_id=config.azure_client_id,
            client_secret=config.azure_client_secret,
            redirect_uri=config.redirect_uri,
            scopes=config.scopes
        )
        self.oauth_provider = MicrosoftProvider(oauth_config, config.azure_tenant_id)
        
        # Set up logging
        if config.debug:
            logging.basicConfig(level=logging.DEBUG)
        
        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register MCP handlers."""
        
        @self.server.list_tools()
        async def list_tools():
            """List available tools."""
            tools = []
            
            # OAuth2 tools
            oauth_tools = create_oauth2_tools(self.oauth_provider)
            tools.extend(oauth_tools)
            
            # Teams-specific tools
            tools.extend([
                create_list_chats_tool(self.teams_client),
                create_create_chat_tool(self.teams_client),
                create_send_message_tool(self.teams_client),
                create_get_messages_tool(self.teams_client)
            ])
            
            return tools
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict):
            """Call a tool."""
            # Get all tools
            tools = await list_tools()
            
            # Find the requested tool
            tool = next((t for t in tools if t.name == name), None)
            if not tool:
                raise ValueError(f"Tool '{name}' not found")
            
            # Call the tool's handler
            handler = getattr(tool, 'handler', None)
            if not handler:
                raise ValueError(f"Tool '{name}' has no handler")
            
            return await handler(arguments)
    
    async def run(self):
        """Run the server."""
        logger.info(f"Starting {self.config.server_name} v{self.config.server_version}")
        
        # Run with stdio transport
        async with stdio_server() as (read_stream, write_stream):
            init_options = InitializationOptions(
                server_name=self.config.server_name,
                server_version=self.config.server_version,
            )
            
            await self.server.run(
                read_stream,
                write_stream,
                init_options
            )


def main():
    """Main entry point."""
    # Load configuration
    config = TeamsConfig()
    
    # Create and run server
    server = TeamsServer(config)
    asyncio.run(server.run())


if __name__ == "__main__":
    main()