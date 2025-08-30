from typing import List, Optional, Dict, Any
from bson import ObjectId
from .base_repository import BaseRepository
from database import budgets_collection

class BudgetRepository(BaseRepository):
    def __init__(self):
        super().__init__(budgets_collection)
    
    async def find_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        return await self.find_by_filter({"user_id": user_id})
    
    async def find_active_budgets(self, user_id: str) -> List[Dict[str, Any]]:
        return await self.find_by_filter({"user_id": user_id, "is_completed": False})
    
    async def find_completed_budgets(self, user_id: str) -> List[Dict[str, Any]]:
        return await self.find_by_filter({"user_id": user_id, "is_completed": True})
    
    async def update_current_amount(self, budget_id: str, amount: float) -> bool:
        result = self.collection.update_one(
            {"_id": ObjectId(budget_id)},
            {"$set": {"current_amount": amount}}
        )
        return result.modified_count > 0
    
    async def increment_current_amount(self, budget_id: str, amount: float) -> bool:
        result = self.collection.update_one(
            {"_id": ObjectId(budget_id)},
            {"$inc": {"current_amount": amount}}
        )
        return result.modified_count > 0
    
    async def mark_as_completed(self, budget_id: str) -> bool:
        result = self.collection.update_one(
            {"_id": ObjectId(budget_id)},
            {"$set": {"is_completed": True}}
        )
        return result.modified_count > 0

budget_repository = BudgetRepository()