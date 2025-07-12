"""Get messages tool."""

import json
from typing import Dict, Any, List
from mcp.types import Tool
from ..api import TeamsClient


def create_get_messages_tool(client: TeamsClient) -> Tool:
    """Create get messages tool."""
    
    async def handler(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get messages from a Teams chat."""
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
            chat_id = arguments["chatId"]
            limit = min(arguments.get("limit", 20), 50)
            order_by = arguments.get("orderBy", "createdDateTime desc")
            
            # Validate order by
            if order_by not in ["createdDateTime desc", "createdDateTime asc"]:
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "error": "Invalid orderBy value",
                        "message": "orderBy must be 'createdDateTime desc' or 'createdDateTime asc'"
                    })
                }]
            
            # Get messages
            messages = await client.get_messages(
                access_token=access_token,
                chat_id=chat_id,
                top=limit,
                order_by=order_by
            )
            
            # Format messages
            formatted_messages = []
            for msg in messages:
                formatted_msg = {
                    "id": msg["id"],
                    "createdDateTime": msg["createdDateTime"],
                    "lastModifiedDateTime": msg.get("lastModifiedDateTime"),
                    "messageType": msg.get("messageType", "message"),
                    "body": {
                        "contentType": msg.get("body", {}).get("contentType"),
                        "content": msg.get("body", {}).get("content")
                    }
                }
                
                # Add sender info if available
                if "from" in msg and msg["from"]:
                    formatted_msg["from"] = {
                        "displayName": msg["from"].get("user", {}).get("displayName"),
                        "id": msg["from"].get("user", {}).get("id")
                    }
                
                # Add attachments info if present
                if msg.get("attachments"):
                    formatted_msg["attachments"] = len(msg["attachments"])
                
                formatted_messages.append(formatted_msg)
            
            return [{
                "type": "text",
                "text": json.dumps({
                    "messages": formatted_messages,
                    "count": len(formatted_messages),
                    "chatId": chat_id,
                    "message": f"Retrieved {len(formatted_messages)} messages"
                })
            }]
            
        except Exception as e:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": str(e),
                    "message": "Failed to get messages"
                })
            }]
    
    tool = Tool(
        name="teams_get_messages",
        description="Get messages from a Teams chat",
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
                "chatId": {
                    "type": "string",
                    "description": "ID of the chat to retrieve messages from"
                },
                "limit": {
                    "type": "number",
                    "description": "Maximum number of messages to return (1-50)",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 20
                },
                "orderBy": {
                    "type": "string",
                    "description": "Sort order for messages",
                    "enum": ["createdDateTime desc", "createdDateTime asc"],
                    "default": "createdDateTime desc"
                }
            },
            "required": ["tokens", "chatId"]
        }
    )
    
    setattr(tool, 'handler', handler)
    return tool