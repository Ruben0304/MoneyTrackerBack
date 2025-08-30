from typing import List, Optional, Dict, Any
from .base_repository import BaseRepository
from database import income_presets_collection
from bson import ObjectId

class IncomePresetRepository(BaseRepository):
    def __init__(self):
        super().__init__(income_presets_collection)
    
    async def find_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        return await self.find_by_filter({"user_id": user_id})
    
    async def find_active_presets(self, user_id: str) -> List[Dict[str, Any]]:
        return await self.find_by_filter({"user_id": user_id, "is_active": True})
    
    async def find_by_collect_day(self, user_id: str, collect_day: int) -> List[Dict[str, Any]]:
        return await self.find_by_filter({"user_id": user_id, "collect_day": collect_day, "is_active": True})
    
    async def toggle_active_status(self, preset_id: str, is_active: bool) -> bool:
        result = self.collection.update_one(
            {"_id": ObjectId(preset_id)},
            {"$set": {"is_active": is_active}}
        )
        return result.modified_count > 0

income_preset_repository = IncomePresetRepository()