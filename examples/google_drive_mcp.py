"""Example: Google Drive MCP server using the OAuth2 library."""

import asyncio
import json
from typing import List, Dict, Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool
import httpx

from mcp_oauth2 import OAuth2Config, GoogleProvider, create_oauth2_tools


class GoogleDriveClient:
    """Simple Google Drive API client."""
    
    def __init__(self):
        self.base_url = "https://www.googleapis.com/drive/v3"
    
    async def list_files(self, access_token: str, query: str = None) -> List[Dict[str, Any]]:
        """List files in Google Drive."""
        params = {"pageSize": 100}
        if query:
            params["q"] = query
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/files",
                headers={"Authorization": f"Bearer {access_token}"},
                params=params
            )
            response.raise_for_status()
            return response.json().get("files", [])


def create_list_files_tool(drive_client: GoogleDriveClient) -> Tool:
    """Create a tool to list Google Drive files."""
    
    async def handler(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        tokens = arguments.get("tokens", {})
        access_token = tokens.get("access_token")
        
        if not access_token:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": "Missing access token",
                    "message": "Please authenticate first using google_is_authenticated"
                })
            }]
        
        try:
            query = arguments.get("query")
            files = await drive_client.list_files(access_token, query)
            
            return [{
                "type": "text",
                "text": json.dumps({
                    "files": files,
                    "count": len(files),
                    "message": f"Found {len(files)} files"
                })
            }]
        except Exception as e:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": str(e),
                    "message": "Failed to list files"
                })
            }]
    
    tool = Tool(
        name="google_drive_list_files",
        description="List files in Google Drive",
        inputSchema={
            "type": "object",
            "properties": {
                "tokens": {
                    "type": "object",
                    "description": "OAuth tokens",
                    "properties": {
                        "access_token": {"type": ["string", "null"]}
                    }
                },
                "query": {
                    "type": "string",
                    "description": "Search query (e.g., \"name contains 'report'\")"
                }
            },
            "required": ["tokens"]
        }
    )
    
    setattr(tool, 'handler', handler)
    return tool


async def main():
    """Run Google Drive MCP server."""
    import os
    
    # Configure OAuth2
    oauth_config = OAuth2Config(
        client_id=os.getenv("GOOGLE_CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET", "YOUR_GOOGLE_CLIENT_SECRET"),
        redirect_uri=os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/callback"),
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    
    # Create providers and clients
    google_provider = GoogleProvider(oauth_config)
    drive_client = GoogleDriveClient()
    
    # Create MCP server
    server = Server("google-drive-mcp")
    
    @server.list_tools()
    async def list_tools():
        tools = []
        
        # Add OAuth2 tools
        tools.extend(create_oauth2_tools(google_provider))
        
        # Add Google Drive tools
        tools.append(create_list_files_tool(drive_client))
        
        return tools
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        tools = await list_tools()
        tool = next((t for t in tools if t.name == name), None)
        
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        
        handler = getattr(tool, 'handler', None)
        if not handler:
            raise ValueError(f"Tool '{name}' has no handler")
        
        return await handler(arguments)
    
    # Run server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


if __name__ == "__main__":
    asyncio.run(main())