"""Teams MCP tools."""

from typing import Any, Dict
from mcp.types import Tool
from .api import TeamsClient


def create_list_chats_tool(client: TeamsClient) -> Tool:
    """Create list chats tool."""
    async def handler(arguments: Dict[str, Any]) -> list:
        access_token = arguments.get("access_token")
        if not access_token:
            raise ValueError("access_token is required")
        
        return await client.list_chats(access_token)
    
    tool = Tool(
        name="teams_list_chats",
        description="List all chats for the authenticated user",
        inputSchema={
            "type": "object",
            "properties": {
                "access_token": {
                    "type": "string",
                    "description": "OAuth access token"
                }
            },
            "required": ["access_token"]
        }
    )
    
    # Attach handler
    setattr(tool, 'handler', handler)
    return tool


def create_create_chat_tool(client: TeamsClient) -> Tool:
    """Create new chat tool."""
    async def handler(arguments: Dict[str, Any]) -> dict:
        access_token = arguments.get("access_token")
        chat_type = arguments.get("chat_type", "oneOnOne")
        members = arguments.get("members", [])
        
        if not access_token:
            raise ValueError("access_token is required")
        if not members:
            raise ValueError("members list is required")
        
        return await client.create_chat(access_token, chat_type, members)
    
    tool = Tool(
        name="teams_create_chat",
        description="Create a new chat",
        inputSchema={
            "type": "object",
            "properties": {
                "access_token": {
                    "type": "string",
                    "description": "OAuth access token"
                },
                "chat_type": {
                    "type": "string",
                    "description": "Type of chat (oneOnOne or group)",
                    "enum": ["oneOnOne", "group"]
                },
                "members": {
                    "type": "array",
                    "description": "List of member email addresses",
                    "items": {"type": "string"}
                }
            },
            "required": ["access_token", "members"]
        }
    )
    
    # Attach handler
    setattr(tool, 'handler', handler)
    return tool


def create_send_message_tool(client: TeamsClient) -> Tool:
    """Create send message tool."""
    async def handler(arguments: Dict[str, Any]) -> dict:
        access_token = arguments.get("access_token")
        chat_id = arguments.get("chat_id")
        content = arguments.get("content")
        
        if not access_token:
            raise ValueError("access_token is required")
        if not chat_id:
            raise ValueError("chat_id is required")
        if not content:
            raise ValueError("content is required")
        
        return await client.send_message(access_token, chat_id, content)
    
    tool = Tool(
        name="teams_send_message",
        description="Send a message to a chat",
        inputSchema={
            "type": "object",
            "properties": {
                "access_token": {
                    "type": "string",
                    "description": "OAuth access token"
                },
                "chat_id": {
                    "type": "string",
                    "description": "Chat ID"
                },
                "content": {
                    "type": "string",
                    "description": "Message content"
                }
            },
            "required": ["access_token", "chat_id", "content"]
        }
    )
    
    # Attach handler
    setattr(tool, 'handler', handler)
    return tool


def create_get_messages_tool(client: TeamsClient) -> Tool:
    """Create get messages tool."""
    async def handler(arguments: Dict[str, Any]) -> list:
        access_token = arguments.get("access_token")
        chat_id = arguments.get("chat_id")
        limit = arguments.get("limit", 50)
        
        if not access_token:
            raise ValueError("access_token is required")
        if not chat_id:
            raise ValueError("chat_id is required")
        
        return await client.get_messages(access_token, chat_id, limit)
    
    tool = Tool(
        name="teams_get_messages",
        description="Get messages from a chat",
        inputSchema={
            "type": "object",
            "properties": {
                "access_token": {
                    "type": "string",
                    "description": "OAuth access token"
                },
                "chat_id": {
                    "type": "string",
                    "description": "Chat ID"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of messages to retrieve",
                    "default": 50
                }
            },
            "required": ["access_token", "chat_id"]
        }
    )
    
    # Attach handler
    setattr(tool, 'handler', handler)
    return tool