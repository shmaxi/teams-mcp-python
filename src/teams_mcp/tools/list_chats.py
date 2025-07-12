"""List chats tool."""

import json
from typing import Dict, Any, List
from mcp.types import Tool
from ..api import TeamsClient


def create_list_chats_tool(client: TeamsClient) -> Tool:
    """Create list chats tool."""
    
    async def handler(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List all chats for the authenticated user."""
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
            filter_query = arguments.get("filter")
            limit = min(arguments.get("limit", 50), 50)
            
            chats = await client.list_chats(
                access_token=access_token,
                filter_query=filter_query,
                top=limit
            )
            
            # Format chat data
            formatted_chats = []
            for chat in chats:
                formatted_chat = {
                    "id": chat["id"],
                    "topic": chat.get("topic", ""),
                    "chatType": chat["chatType"],
                    "createdDateTime": chat.get("createdDateTime"),
                    "lastUpdatedDateTime": chat.get("lastUpdatedDateTime")
                }
                
                # Add member info if available
                if "members" in chat:
                    formatted_chat["members"] = [
                        {
                            "displayName": m.get("displayName"),
                            "email": m.get("email")
                        }
                        for m in chat["members"]
                    ]
                
                formatted_chats.append(formatted_chat)
            
            return [{
                "type": "text",
                "text": json.dumps({
                    "chats": formatted_chats,
                    "count": len(formatted_chats),
                    "message": f"Found {len(formatted_chats)} chats"
                })
            }]
            
        except Exception as e:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": str(e),
                    "message": "Failed to list chats"
                })
            }]
    
    tool = Tool(
        name="teams_list_chats",
        description="List all chats for the authenticated user",
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
                "filter": {
                    "type": ["string", "null"],
                    "description": "OData filter expression (e.g., \"chatType eq 'oneOnOne'\")"
                },
                "limit": {
                    "type": "number",
                    "description": "Maximum number of chats to return (1-50)",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 50
                }
            },
            "required": []
        }
    )
    
    setattr(tool, 'handler', handler)
    return tool