from fastapi import APIRouter, HTTPException, status
from typing import List
from models import Category
from repositories.category_repository import category_repository
from bson import ObjectId

router = APIRouter(prefix="/categories", tags=["categories"])

def category_helper(category) -> dict:
    return {
        "id": str(category["_id"]),
        "name": category["name"],
        "icon": category["icon"],
        "color": category["color"],
        "type": category["type"]
    }

@router.get("/", response_model=List[dict])
async def get_all_categories():
    categories = await category_repository.find_all()
    return [category_helper(category) for category in categories]

@router.get("/expense", response_model=List[dict])
async def get_expense_categories():
    categories = await category_repository.find_by_type("expense")
    return [category_helper(category) for category in categories]

@router.get("/income", response_model=List[dict])
async def get_income_categories():
    categories = await category_repository.find_by_type("income")
    return [category_helper(category) for category in categories]

@router.get("/{category_id}")
async def get_category(category_id: str):
    if not ObjectId.is_valid(category_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category ID"
        )
    
    category = await category_repository.find_by_id(category_id)
    if category:
        return category_helper(category)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Category not found"
    )

@router.post("/", response_model=dict)
async def create_category(category: Category):
    # Check if category with same name already exists
    existing = await category_repository.find_one_by_filter({"name": category.name, "type": category.type})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists"
        )
    
    category_dict = {
        "name": category.name,
        "icon": category.icon,
        "color": category.color,
        "type": category.type
    }
    
    category_id = await category_repository.create(category_dict)
    new_category = await category_repository.find_by_id(category_id)
    return category_helper(new_category)

@router.put("/{category_id}")
async def update_category(category_id: str, category_update: dict):
    if not ObjectId.is_valid(category_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category ID"
        )
    
    success = await category_repository.update_by_id(category_id, category_update)
    
    if success:
        updated_category = await category_repository.find_by_id(category_id)
        return category_helper(updated_category)
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Category not found"
    )

@router.delete("/{category_id}")
async def delete_category(category_id: str):
    if not ObjectId.is_valid(category_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category ID"
        )
    
    success = await category_repository.delete_by_id(category_id)
    if success:
        return {"message": "Category deleted successfully"}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Category not found"
    )