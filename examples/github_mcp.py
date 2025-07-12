"""Example: GitHub MCP server using the OAuth2 library."""

import asyncio
import json
from typing import List, Dict, Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool
import httpx

from mcp_oauth2 import OAuth2Config, GenericOAuth2Provider, create_oauth2_tools


class GitHubClient:
    """Simple GitHub API client."""
    
    def __init__(self):
        self.base_url = "https://api.github.com"
    
    async def get_user(self, access_token: str) -> Dict[str, Any]:
        """Get authenticated user info."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def list_repos(self, access_token: str, visibility: str = "all") -> List[Dict[str, Any]]:
        """List user's repositories."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/user/repos",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                },
                params={"visibility": visibility, "per_page": 100}
            )
            response.raise_for_status()
            return response.json()


def create_github_tools(github_client: GitHubClient) -> List[Tool]:
    """Create GitHub-specific tools."""
    tools = []
    
    # Get user info tool
    async def get_user_handler(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        tokens = arguments.get("tokens", {})
        access_token = tokens.get("access_token")
        
        if not access_token:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": "Missing access token",
                    "message": "Please authenticate first using github_is_authenticated"
                })
            }]
        
        try:
            user = await github_client.get_user(access_token)
            return [{
                "type": "text",
                "text": json.dumps({
                    "user": {
                        "login": user["login"],
                        "name": user.get("name"),
                        "email": user.get("email"),
                        "public_repos": user.get("public_repos"),
                        "followers": user.get("followers")
                    },
                    "message": "Successfully retrieved user info"
                })
            }]
        except Exception as e:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": str(e),
                    "message": "Failed to get user info"
                })
            }]
    
    user_tool = Tool(
        name="github_get_user",
        description="Get authenticated GitHub user info",
        inputSchema={
            "type": "object",
            "properties": {
                "tokens": {
                    "type": "object",
                    "description": "OAuth tokens",
                    "properties": {
                        "access_token": {"type": ["string", "null"]}
                    }
                }
            },
            "required": ["tokens"]
        }
    )
    setattr(user_tool, 'handler', get_user_handler)
    tools.append(user_tool)
    
    # List repos tool
    async def list_repos_handler(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        tokens = arguments.get("tokens", {})
        access_token = tokens.get("access_token")
        
        if not access_token:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": "Missing access token",
                    "message": "Please authenticate first using github_is_authenticated"
                })
            }]
        
        try:
            visibility = arguments.get("visibility", "all")
            repos = await github_client.list_repos(access_token, visibility)
            
            formatted_repos = [
                {
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "private": repo["private"],
                    "description": repo.get("description"),
                    "language": repo.get("language"),
                    "stars": repo.get("stargazers_count", 0),
                    "url": repo["html_url"]
                }
                for repo in repos
            ]
            
            return [{
                "type": "text",
                "text": json.dumps({
                    "repos": formatted_repos,
                    "count": len(formatted_repos),
                    "message": f"Found {len(formatted_repos)} repositories"
                })
            }]
        except Exception as e:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": str(e),
                    "message": "Failed to list repositories"
                })
            }]
    
    repos_tool = Tool(
        name="github_list_repos",
        description="List GitHub repositories",
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
                "visibility": {
                    "type": "string",
                    "description": "Filter by visibility",
                    "enum": ["all", "public", "private"],
                    "default": "all"
                }
            },
            "required": ["tokens"]
        }
    )
    setattr(repos_tool, 'handler', list_repos_handler)
    tools.append(repos_tool)
    
    return tools


async def main():
    """Run GitHub MCP server."""
    import os
    
    # Configure OAuth2 for GitHub
    oauth_config = OAuth2Config(
        client_id=os.getenv("GITHUB_CLIENT_ID", "YOUR_GITHUB_CLIENT_ID"),
        client_secret=os.getenv("GITHUB_CLIENT_SECRET", "YOUR_GITHUB_CLIENT_SECRET"),
        redirect_uri=os.getenv("GITHUB_REDIRECT_URI", "http://localhost:3000/auth/callback"),
        scopes=["user", "repo"],
        authorization_endpoint="https://github.com/login/oauth/authorize",
        token_endpoint="https://github.com/login/oauth/access_token"
    )
    
    # Create providers and clients
    github_provider = GenericOAuth2Provider("github", oauth_config)
    github_client = GitHubClient()
    
    # Create MCP server
    server = Server("github-mcp")
    
    @server.list_tools()
    async def list_tools():
        tools = []
        
        # Add OAuth2 tools
        tools.extend(create_oauth2_tools(github_provider))
        
        # Add GitHub-specific tools
        tools.extend(create_github_tools(github_client))
        
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