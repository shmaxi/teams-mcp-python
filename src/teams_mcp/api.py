"""Teams API client implementation."""

import logging
from typing import List, Dict, Any, Optional
import aiohttp

logger = logging.getLogger(__name__)


class TeamsClient:
    """Microsoft Teams API client."""
    
    def __init__(self):
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close the client session."""
        if self.session:
            await self.session.close()
    
    async def list_chats(self, access_token: str) -> List[Dict[str, Any]]:
        """List user's chats."""
        await self._ensure_session()
        
        headers = {"Authorization": f"Bearer {access_token}"}
        async with self.session.get(f"{self.base_url}/me/chats", headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data.get("value", [])
    
    async def create_chat(self, access_token: str, chat_type: str, members: List[str]) -> Dict[str, Any]:
        """Create a new chat."""
        await self._ensure_session()
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Build members list
        members_data = []
        for member_email in members:
            members_data.append({
                "@odata.type": "#microsoft.graph.aadUserConversationMember",
                "roles": ["owner"],
                "user@odata.bind": f"https://graph.microsoft.com/v1.0/users/{member_email}"
            })
        
        payload = {
            "chatType": chat_type,
            "members": members_data
        }
        
        async with self.session.post(f"{self.base_url}/chats", headers=headers, json=payload) as resp:
            resp.raise_for_status()
            return await resp.json()
    
    async def send_message(self, access_token: str, chat_id: str, content: str) -> Dict[str, Any]:
        """Send a message to a chat."""
        await self._ensure_session()
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "body": {
                "content": content
            }
        }
        
        async with self.session.post(
            f"{self.base_url}/chats/{chat_id}/messages", 
            headers=headers, 
            json=payload
        ) as resp:
            resp.raise_for_status()
            return await resp.json()
    
    async def get_messages(self, access_token: str, chat_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get messages from a chat."""
        await self._ensure_session()
        
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"$top": limit}
        
        async with self.session.get(
            f"{self.base_url}/chats/{chat_id}/messages",
            headers=headers,
            params=params
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data.get("value", [])