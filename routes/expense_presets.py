from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from bson import ObjectId
from datetime import datetime

from models import (
    ExpensePreset, ExpensePresetCreate, ExpensePresetUpdate,
    TransactionCreate, Transaction
)
from database import (
    expense_presets_collection, transactions_collection, 
    accounts_collection
)
from auth import get_current_user

router = APIRouter()

@router.post("/", response_model=dict)
async def create_expense_preset(
    expense_preset: ExpensePresetCreate,
    current_user: dict = Depends(get_current_user)
):
    expense_preset_dict = expense_preset.dict()
    expense_preset_dict["user_id"] = str(current_user["_id"])
    expense_preset_dict["created_at"] = datetime.utcnow()
    expense_preset_dict["updated_at"] = datetime.utcnow()
    
    result = expense_presets_collection.insert_one(expense_preset_dict)
    
    created_preset = expense_presets_collection.find_one({"_id": result.inserted_id})
    created_preset["id"] = str(created_preset["_id"])
    created_preset.pop("_id")
    
    return {"message": "Expense preset created successfully", "data": created_preset}

@router.get("/", response_model=dict)
async def get_expense_presets(current_user: dict = Depends(get_current_user)):
    presets = list(expense_presets_collection.find({"user_id": str(current_user["_id"])}))
    
    for preset in presets:
        preset["id"] = str(preset["_id"])
        preset.pop("_id")
    
    return {"data": presets}

@router.get("/{preset_id}", response_model=dict)
async def get_expense_preset(
    preset_id: str,
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(preset_id):
        raise HTTPException(status_code=400, detail="Invalid preset ID")
    
    preset = expense_presets_collection.find_one({
        "_id": ObjectId(preset_id),
        "user_id": str(current_user["_id"])
    })
    
    if not preset:
        raise HTTPException(status_code=404, detail="Expense preset not found")
    
    preset["id"] = str(preset["_id"])
    preset.pop("_id")
    
    return {"data": preset}

@router.put("/{preset_id}", response_model=dict)
async def update_expense_preset(
    preset_id: str,
    preset_update: ExpensePresetUpdate,
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(preset_id):
        raise HTTPException(status_code=400, detail="Invalid preset ID")
    
    update_data = {k: v for k, v in preset_update.dict(exclude_unset=True).items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    update_data["updated_at"] = datetime.utcnow()
    
    result = expense_presets_collection.update_one(
        {"_id": ObjectId(preset_id), "user_id": str(current_user["_id"])},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Expense preset not found")
    
    return {"message": "Expense preset updated successfully"}

@router.delete("/{preset_id}", response_model=dict)
async def delete_expense_preset(
    preset_id: str,
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(preset_id):
        raise HTTPException(status_code=400, detail="Invalid preset ID")
    
    result = expense_presets_collection.delete_one({
        "_id": ObjectId(preset_id),
        "user_id": str(current_user["_id"])
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Expense preset not found")
    
    return {"message": "Expense preset deleted successfully"}

@router.post("/{preset_id}/use", response_model=dict)
async def use_expense_preset(
    preset_id: str,
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(preset_id):
        raise HTTPException(status_code=400, detail="Invalid preset ID")
    
    preset = expense_presets_collection.find_one({
        "_id": ObjectId(preset_id),
        "user_id": str(current_user["_id"])
    })
    
    if not preset:
        raise HTTPException(status_code=404, detail="Expense preset not found")
    
    if not preset.get("is_active", True):
        raise HTTPException(status_code=400, detail="Expense preset is not active")
    
    account = accounts_collection.find_one({
        "_id": ObjectId(preset["account_id"]),
        "user_id": str(current_user["_id"])
    })
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if account["balance"] < preset["amount"]:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    transaction_data = TransactionCreate(
        account_id=preset["account_id"],
        amount=preset["amount"],
        type="expense",
        category=preset["category"],
        description=preset.get("description", preset["name"])
    )
    
    transaction_dict = transaction_data.dict()
    transaction_dict["user_id"] = str(current_user["_id"])
    transaction_dict["date"] = datetime.utcnow()
    transaction_dict["currency"] = preset["currency"]
    
    result = transactions_collection.insert_one(transaction_dict)
    
    new_balance = account["balance"] - preset["amount"]
    accounts_collection.update_one(
        {"_id": ObjectId(preset["account_id"])},
        {"$set": {"balance": new_balance, "updated_at": datetime.utcnow()}}
    )
    
    created_transaction = transactions_collection.find_one({"_id": result.inserted_id})
    created_transaction["id"] = str(created_transaction["_id"])
    created_transaction.pop("_id")
    
    return {
        "message": "Expense registered successfully from preset",
        "transaction": created_transaction
    }