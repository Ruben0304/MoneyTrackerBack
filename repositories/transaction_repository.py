from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from .base_repository import BaseRepository
from database import transactions_collection

class TransactionRepository(BaseRepository):
    def __init__(self):
        super().__init__(transactions_collection)
    
    async def find_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        return list(self.collection.find({"user_id": user_id}).sort("date", -1))
    
    async def find_by_account_id(self, account_id: str) -> List[Dict[str, Any]]:
        return list(self.collection.find({"account_id": account_id}).sort("date", -1))
    
    async def find_by_user_and_type(self, user_id: str, transaction_type: str) -> List[Dict[str, Any]]:
        return list(self.collection.find({"user_id": user_id, "type": transaction_type}).sort("date", -1))
    
    async def find_by_date_range(self, user_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        return list(self.collection.find({
            "user_id": user_id,
            "date": {"$gte": start_date, "$lte": end_date}
        }).sort("date", -1))
    
    async def find_by_category(self, user_id: str, category: str) -> List[Dict[str, Any]]:
        return list(self.collection.find({"user_id": user_id, "category": category}).sort("date", -1))
    
    async def get_total_by_type_and_period(self, user_id: str, transaction_type: str, start_date: datetime, end_date: datetime) -> float:
        pipeline = [
            {"$match": {
                "user_id": user_id,
                "type": transaction_type,
                "date": {"$gte": start_date, "$lte": end_date}
            }},
            {"$group": {
                "_id": None,
                "total": {"$sum": "$amount"}
            }}
        ]
        result = list(self.collection.aggregate(pipeline))
        return result[0]["total"] if result else 0.0

transaction_repository = TransactionRepository()