from typing import List, Optional, Dict, Any
from bson import ObjectId
from .base_repository import BaseRepository
from database import accounts_collection

class AccountRepository(BaseRepository):
    def __init__(self):
        super().__init__(accounts_collection)
    
    async def find_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        return await self.find_by_filter({"user_id": user_id})
    
    async def find_by_user_and_type(self, user_id: str, account_type: str) -> List[Dict[str, Any]]:
        return await self.find_by_filter({"user_id": user_id, "type": account_type})
    
    async def update_balance(self, account_id: str, new_balance: float) -> bool:
        result = self.collection.update_one(
            {"_id": ObjectId(account_id)},
            {"$set": {"balance": new_balance}}
        )
        return result.modified_count > 0
    
    async def increment_balance(self, account_id: str, amount: float) -> bool:
        result = self.collection.update_one(
            {"_id": ObjectId(account_id)},
            {"$inc": {"balance": amount}}
        )
        return result.modified_count > 0

account_repository = AccountRepository()