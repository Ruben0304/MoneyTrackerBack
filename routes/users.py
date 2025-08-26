from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from models import User, UserCreate, UserLogin, UserUpdate
from database import users_collection
from auth import get_current_active_user, user_helper, require_role
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/users", tags=["users"])

# User creation is now handled by auth/register endpoint

@router.get("/", response_model=List[dict])
async def get_users(current_user: dict = Depends(require_role(["max"]))):
    """Get all users - only max role can access"""
    users = []
    for user in users_collection.find():
        users.append(user_helper(user))
    return users

@router.get("/{user_id}")
async def get_user(user_id: str, current_user: dict = Depends(get_current_active_user)):
    """Get user by ID - users can only access their own data unless they have max role"""
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    # Allow access if it's the current user or if current user has max role
    if str(current_user["_id"]) != user_id and current_user.get("role") != "max":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user:
        return user_helper(user)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )

@router.put("/{user_id}")
async def update_user(
    user_id: str, 
    user_update: UserUpdate, 
    current_user: dict = Depends(get_current_active_user)
):
    """Update user - only max role can update other users"""
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    # Allow access if it's the current user or if current user has max role
    if str(current_user["_id"]) != user_id and current_user.get("role") != "max":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    update_data = user_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    result = users_collection.update_one(
        {"_id": ObjectId(user_id)}, 
        {"$set": update_data}
    )
    
    if result.modified_count == 1:
        updated_user = users_collection.find_one({"_id": ObjectId(user_id)})
        return user_helper(updated_user)
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )

@router.delete("/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(require_role(["max"]))):
    """Delete user - only max role can delete users"""
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    result = users_collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 1:
        return {"message": "User deleted successfully"}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )