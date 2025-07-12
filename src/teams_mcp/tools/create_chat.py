"""Create chat tool."""

import json
from typing import Dict, Any, List
from mcp.types import Tool
from ..api import TeamsClient


def create_create_chat_tool(client: TeamsClient) -> Tool:
    """Create chat tool."""
    
    async def handler(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create a new Teams chat."""
        tokens = arguments.get("tokens", {})
        access_token = tokens.get("access_token")
        
        if not access_token:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": "Missing access token",
                    "message": "Please authenticate first using teams_is_authenticated"
                })
            }]
        
        try:
            chat_type = arguments["chatType"]
            members = arguments["members"]
            topic = arguments.get("topic")
            
            # Validate chat type
            if chat_type not in ["oneOnOne", "group"]:
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "error": "Invalid chat type",
                        "message": "chatType must be 'oneOnOne' or 'group'"
                    })
                }]
            
            # Validate members
            if not members or not isinstance(members, list):
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "error": "Invalid members",
                        "message": "At least one member is required"
                    })
                }]
            
            if chat_type == "oneOnOne" and len(members) != 1:
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "error": "Invalid members count",
                        "message": "One-on-one chat requires exactly one other member"
                    })
                }]
            
            # Create the chat
            chat = await client.create_chat(
                access_token=access_token,
                chat_type=chat_type,
                members=members,
                topic=topic
            )
            
            return [{
                "type": "text",
                "text": json.dumps({
                    "chat": {
                        "id": chat["id"],
                        "chatType": chat["chatType"],
                        "topic": chat.get("topic", ""),
                        "createdDateTime": chat.get("createdDateTime"),
                        "webUrl": chat.get("webUrl")
                    },
                    "message": f"Successfully created {chat_type} chat"
                })
            }]
            
        except Exception as e:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": str(e),
                    "message": "Failed to create chat"
                })
            }]
    
    tool = Tool(
        name="teams_create_chat",
        description="Create a new Teams chat (one-on-one or group)",
        inputSchema={
            "type": "object",
            "properties": {
                "tokens": {
                    "type": "object",
                    "description": "OAuth tokens with access_token",
                    "properties": {
                        "access_token": {"type": ["string", "null"]}
                    },
                    "required": []
                },
                "chatType": {
                    "type": "string",
                    "description": "Type of chat to create",
                    "enum": ["oneOnOne", "group"]
                },
                "members": {
                    "type": "array",
                    "description": "List of members to add to the chat",
                    "items": {
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "Email address of the user to add"
                            },
                            "role": {
                                "type": "string",
                                "description": "Role of the member in the chat",
                                "enum": ["owner", "guest"],
                                "default": "owner"
                            }
                        },
                        "required": ["email"]
                    },
                    "minItems": 1
                },
                "topic": {
                    "type": "string",
                    "description": "Topic/name for the chat (only for group chats)"
                }
            },
            "required": ["tokens", "chatType", "members"]
        }
    )
    
    setattr(tool, 'handler', handler)
    return tool