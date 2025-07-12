"""Teams API client."""

import httpx
from typing import Dict, Any, Optional, List
from .rate_limiter import RateLimiter


class TeamsClient:
    """Microsoft Teams API client using Graph API."""
    
    def __init__(self, rate_limiter: Optional[RateLimiter] = None):
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.rate_limiter = rate_limiter or RateLimiter()
    
    def _get_headers(self, access_token: str) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        access_token: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make rate-limited API request."""
        async def make_request():
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method,
                    f"{self.base_url}{endpoint}",
                    headers=self._get_headers(access_token),
                    **kwargs
                )
                response.raise_for_status()
                return response.json() if response.content else {}
        
        return await self.rate_limiter.execute_with_retry(make_request)
    
    async def list_chats(
        self,
        access_token: str,
        filter_query: Optional[str] = None,
        top: int = 50
    ) -> List[Dict[str, Any]]:
        """List user's chats."""
        params = {"$top": top}
        if filter_query:
            params["$filter"] = filter_query
        
        result = await self._request(
            "GET",
            "/me/chats",
            access_token,
            params=params
        )
        return result.get("value", [])
    
    async def create_chat(
        self,
        access_token: str,
        chat_type: str,
        members: List[Dict[str, Any]],
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new chat."""
        # Get current user ID first
        user_info = await self._request("GET", "/me", access_token)
        current_user_id = user_info["id"]
        
        # Format members
        formatted_members = []
        for member in members:
            formatted_members.append({
                "@odata.type": "#microsoft.graph.aadUserConversationMember",
                "roles": [member.get("role", "owner")],
                "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{member['email']}')"
            })
        
        # Add current user as owner if not already included
        current_user_included = any(
            m.get("user@odata.bind", "").endswith(f"'{current_user_id}')")
            for m in formatted_members
        )
        if not current_user_included:
            formatted_members.insert(0, {
                "@odata.type": "#microsoft.graph.aadUserConversationMember",
                "roles": ["owner"],
                "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{current_user_id}')"
            })
        
        body = {
            "chatType": chat_type,
            "members": formatted_members
        }
        
        if topic and chat_type == "group":
            body["topic"] = topic
        
        return await self._request(
            "POST",
            "/chats",
            access_token,
            json=body
        )
    
    async def send_message(
        self,
        access_token: str,
        chat_id: str,
        content: str,
        content_type: str = "text"
    ) -> Dict[str, Any]:
        """Send a message to a chat."""
        body = {
            "body": {
                "contentType": content_type,
                "content": content
            }
        }
        
        return await self._request(
            "POST",
            f"/chats/{chat_id}/messages",
            access_token,
            json=body
        )
    
    async def get_messages(
        self,
        access_token: str,
        chat_id: str,
        top: int = 20,
        order_by: str = "createdDateTime desc"
    ) -> List[Dict[str, Any]]:
        """Get messages from a chat."""
        params = {
            "$top": top,
            "$orderby": order_by
        }
        
        result = await self._request(
            "GET",
            f"/chats/{chat_id}/messages",
            access_token,
            params=params
        )
        return result.get("value", [])