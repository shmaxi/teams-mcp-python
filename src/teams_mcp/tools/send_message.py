"""Send message tool."""

import json
from typing import Dict, Any, List
from mcp.types import Tool
from ..api import TeamsClient


def create_send_message_tool(client: TeamsClient) -> Tool:
    """Create send message tool."""
    
    async def handler(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Send a message to a Teams chat."""
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
            content = arguments["content"]
            content_type = arguments.get("contentType", "text")
            
            # Validate content type
            if content_type not in ["text", "html"]:
                return [{
                    "type": "text",
                    "text": json.dumps({
                        "error": "Invalid content type",
                        "message": "contentType must be 'text' or 'html'"
                    })
                }]
            
            # Send the message
            message = await client.send_message(
                access_token=access_token,
                chat_id=chat_id,
                content=content,
                content_type=content_type
            )
            
            return [{
                "type": "text",
                "text": json.dumps({
                    "message": {
                        "id": message["id"],
                        "createdDateTime": message["createdDateTime"],
                        "from": {
                            "displayName": message.get("from", {}).get("user", {}).get("displayName"),
                            "id": message.get("from", {}).get("user", {}).get("id")
                        },
                        "body": {
                            "contentType": message.get("body", {}).get("contentType"),
                            "content": message.get("body", {}).get("content")
                        }
                    },
                    "message": "Message sent successfully"
                })
            }]
            
        except Exception as e:
            return [{
                "type": "text",
                "text": json.dumps({
                    "error": str(e),
                    "message": "Failed to send message"
                })
            }]
    
    tool = Tool(
        name="teams_send_message",
        description="Send a message to a Teams chat",
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
                    "description": "ID of the chat to send the message to"
                },
                "content": {
                    "type": "string",
                    "description": "Content of the message"
                },
                "contentType": {
                    "type": "string",
                    "description": "Type of content (text or HTML)",
                    "enum": ["text", "html"],
                    "default": "text"
                }
            },
            "required": ["tokens", "chatId", "content"]
        }
    )
    
    setattr(tool, 'handler', handler)
    return tool