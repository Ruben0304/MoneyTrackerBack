from typing import List, Optional, Dict, Any
from .base_repository import BaseRepository
from database import users_collection
from bson import ObjectId

class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__(users_collection)
    
    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return await self.find_one_by_filter({"email": email})
    
    async def find_active_users(self) -> List[Dict[str, Any]]:
        return await self.find_by_filter({"is_active": True})
    
    async def increment_ai_requests(self, user_id: str) -> bool:
        result = self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {"ai_requests_used": 1}}
        )
        return result.modified_count > 0
    
    async def reset_ai_requests(self, user_id: str) -> bool:
        result = self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"ai_requests_used": 0}}
        )
        return result.modified_count > 0

user_repository = UserRepository()