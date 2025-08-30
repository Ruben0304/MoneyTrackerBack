from typing import List, Optional, Dict, Any
from bson import ObjectId
from .base_repository import BaseRepository
from database import auto_savings_collection
from bson import ObjectId

class AutoSavingsRepository(BaseRepository):
    def __init__(self):
        super().__init__(auto_savings_collection)
    
    async def find_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.find_one_by_filter({"user_id": user_id})
    
    async def find_active_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.find_one_by_filter({"user_id": user_id, "is_active": True})
    
    async def toggle_active_status(self, user_id: str, is_active: bool) -> bool:
        result = self.collection.update_one(
            {"user_id": user_id},
            {"$set": {"is_active": is_active}}
        )
        return result.modified_count > 0
    
    async def update_percentage(self, user_id: str, percentage: float) -> bool:
        result = self.collection.update_one(
            {"user_id": user_id},
            {"$set": {"percentage": percentage}}
        )
        return result.modified_count > 0

auto_savings_repository = AutoSavingsRepository()