from fastapi import APIRouter, HTTPException, status
from typing import List
from models import Category
from database import categories_collection
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
    categories = []
    for category in categories_collection.find():
        categories.append(category_helper(category))
    return categories

@router.get("/expense", response_model=List[dict])
async def get_expense_categories():
    categories = []
    for category in categories_collection.find({"type": "expense"}):
        categories.append(category_helper(category))
    return categories

@router.get("/income", response_model=List[dict])
async def get_income_categories():
    categories = []
    for category in categories_collection.find({"type": "income"}):
        categories.append(category_helper(category))
    return categories

@router.get("/{category_id}")
async def get_category(category_id: str):
    if not ObjectId.is_valid(category_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category ID"
        )
    
    category = categories_collection.find_one({"_id": ObjectId(category_id)})
    if category:
        return category_helper(category)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Category not found"
    )

@router.post("/", response_model=dict)
async def create_category(category: Category):
    # Check if category with same name already exists
    existing = categories_collection.find_one({"name": category.name, "type": category.type})
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
    
    result = categories_collection.insert_one(category_dict)
    new_category = categories_collection.find_one({"_id": result.inserted_id})
    return category_helper(new_category)

@router.put("/{category_id}")
async def update_category(category_id: str, category_update: dict):
    if not ObjectId.is_valid(category_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid category ID"
        )
    
    result = categories_collection.update_one(
        {"_id": ObjectId(category_id)}, 
        {"$set": category_update}
    )
    
    if result.modified_count == 1:
        updated_category = categories_collection.find_one({"_id": ObjectId(category_id)})
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
    
    result = categories_collection.delete_one({"_id": ObjectId(category_id)})
    if result.deleted_count == 1:
        return {"message": "Category deleted successfully"}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Category not found"
    )