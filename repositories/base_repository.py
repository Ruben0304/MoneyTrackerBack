from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from bson import ObjectId
from pymongo.collection import Collection

class BaseRepository(ABC):
    def __init__(self, collection: Collection):
        self.collection = collection
    
    async def create(self, data: Dict[str, Any]) -> str:
        result = self.collection.insert_one(data)
        return str(result.inserted_id)
    
    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        return self.collection.find_one({"_id": ObjectId(id)})
    
    async def find_all(self) -> List[Dict[str, Any]]:
        return list(self.collection.find())
    
    async def update_by_id(self, id: str, data: Dict[str, Any]) -> bool:
        result = self.collection.update_one(
            {"_id": ObjectId(id)}, 
            {"$set": data}
        )
        return result.modified_count > 0
    
    async def delete_by_id(self, id: str) -> bool:
        result = self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
    
    async def find_by_filter(self, filter_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        return list(self.collection.find(filter_dict))
    
    async def find_one_by_filter(self, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.collection.find_one(filter_dict)