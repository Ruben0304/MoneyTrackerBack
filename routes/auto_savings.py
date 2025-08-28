from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from bson import ObjectId
from datetime import datetime

from models import (
    AutoSavings, AutoSavingsCreate, AutoSavingsUpdate
)
from database import (
    auto_savings_collection, accounts_collection
)
from auth import get_current_user

router = APIRouter()

@router.post("/", response_model=dict)
async def create_auto_savings(
    auto_savings: AutoSavingsCreate,
    current_user: dict = Depends(get_current_user)
):
    if auto_savings.percentage <= 0 or auto_savings.percentage > 100:
        raise HTTPException(status_code=400, detail="Percentage must be between 1 and 100")
    
    savings_account = accounts_collection.find_one({
        "_id": ObjectId(auto_savings.savings_account_id),
        "user_id": str(current_user["_id"]),
        "type": "ahorro"
    })
    
    if not savings_account:
        raise HTTPException(status_code=404, detail="Savings account not found")
    
    existing_settings = auto_savings_collection.find_one({
        "user_id": str(current_user["_id"])
    })
    
    if existing_settings:
        raise HTTPException(
            status_code=400, 
            detail="Auto savings already configured. Use PUT to update settings."
        )
    
    auto_savings_dict = auto_savings.dict()
    auto_savings_dict["user_id"] = str(current_user["_id"])
    auto_savings_dict["created_at"] = datetime.utcnow()
    auto_savings_dict["updated_at"] = datetime.utcnow()
    
    result = auto_savings_collection.insert_one(auto_savings_dict)
    
    created_settings = auto_savings_collection.find_one({"_id": result.inserted_id})
    created_settings["id"] = str(created_settings["_id"])
    created_settings.pop("_id")
    
    return {"message": "Auto savings configured successfully", "data": created_settings}

@router.get("/", response_model=dict)
async def get_auto_savings(current_user: dict = Depends(get_current_user)):
    settings = auto_savings_collection.find_one({"user_id": str(current_user["_id"])})
    
    if not settings:
        return {"data": None}
    
    settings["id"] = str(settings["_id"])
    settings.pop("_id")
    
    savings_account = accounts_collection.find_one({
        "_id": ObjectId(settings["savings_account_id"])
    })
    
    if savings_account:
        settings["savings_account_name"] = savings_account["name"]
        settings["savings_account_currency"] = savings_account["currency"]
    
    return {"data": settings}

@router.put("/", response_model=dict)
async def update_auto_savings(
    auto_savings_update: AutoSavingsUpdate,
    current_user: dict = Depends(get_current_user)
):
    existing_settings = auto_savings_collection.find_one({
        "user_id": str(current_user["_id"])
    })
    
    if not existing_settings:
        raise HTTPException(status_code=404, detail="Auto savings not configured")
    
    update_data = {k: v for k, v in auto_savings_update.dict(exclude_unset=True).items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    if "percentage" in update_data:
        if update_data["percentage"] <= 0 or update_data["percentage"] > 100:
            raise HTTPException(status_code=400, detail="Percentage must be between 1 and 100")
    
    if "savings_account_id" in update_data:
        savings_account = accounts_collection.find_one({
            "_id": ObjectId(update_data["savings_account_id"]),
            "user_id": str(current_user["_id"]),
            "type": "ahorro"
        })
        
        if not savings_account:
            raise HTTPException(status_code=404, detail="Savings account not found")
    
    update_data["updated_at"] = datetime.utcnow()
    
    auto_savings_collection.update_one(
        {"user_id": str(current_user["_id"])},
        {"$set": update_data}
    )
    
    return {"message": "Auto savings updated successfully"}

@router.delete("/", response_model=dict)
async def delete_auto_savings(current_user: dict = Depends(get_current_user)):
    result = auto_savings_collection.delete_one({
        "user_id": str(current_user["_id"])
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Auto savings not found")
    
    return {"message": "Auto savings configuration deleted successfully"}

@router.post("/toggle", response_model=dict)
async def toggle_auto_savings(current_user: dict = Depends(get_current_user)):
    settings = auto_savings_collection.find_one({"user_id": str(current_user["_id"])})
    
    if not settings:
        raise HTTPException(status_code=404, detail="Auto savings not configured")
    
    new_status = not settings.get("is_active", True)
    
    auto_savings_collection.update_one(
        {"user_id": str(current_user["_id"])},
        {"$set": {"is_active": new_status, "updated_at": datetime.utcnow()}}
    )
    
    status_text = "enabled" if new_status else "disabled"
    return {"message": f"Auto savings {status_text} successfully", "is_active": new_status}