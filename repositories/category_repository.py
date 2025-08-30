from typing import List, Optional, Dict, Any
from .base_repository import BaseRepository
from database import categories_collection

class CategoryRepository(BaseRepository):
    def __init__(self):
        super().__init__(categories_collection)
    
    async def find_by_type(self, category_type: str) -> List[Dict[str, Any]]:
        return await self.find_by_filter({"type": category_type})
    
    async def find_income_categories(self) -> List[Dict[str, Any]]:
        return await self.find_by_type("income")
    
    async def find_expense_categories(self) -> List[Dict[str, Any]]:
        return await self.find_by_type("expense")

category_repository = CategoryRepository()