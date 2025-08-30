from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from bson import ObjectId
from datetime import datetime

from models import (
    ExpensePreset, ExpensePresetCreate, ExpensePresetUpdate,
    TransactionCreate, Transaction
)
from repositories.expense_preset_repository import expense_preset_repository
from repositories.transaction_repository import transaction_repository
from repositories.account_repository import account_repository
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
    
    preset_id = await expense_preset_repository.create(expense_preset_dict)
    
    created_preset = await expense_preset_repository.find_by_id(preset_id)
    created_preset["id"] = str(created_preset["_id"])
    created_preset.pop("_id")
    
    return {"message": "Expense preset created successfully", "data": created_preset}

@router.get("/", response_model=dict)
async def get_expense_presets(current_user: dict = Depends(get_current_user)):
    presets = await expense_preset_repository.find_by_user_id(str(current_user["_id"]))
    
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
    
    preset = await expense_preset_repository.find_one_by_filter({
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
    
    # Check if preset exists and belongs to user
    existing_preset = await expense_preset_repository.find_one_by_filter({
        "_id": ObjectId(preset_id), 
        "user_id": str(current_user["_id"])
    })
    
    if not existing_preset:
        raise HTTPException(status_code=404, detail="Expense preset not found")
    
    await expense_preset_repository.update_by_id(preset_id, update_data)
    
    return {"message": "Expense preset updated successfully"}

@router.delete("/{preset_id}", response_model=dict)
async def delete_expense_preset(
    preset_id: str,
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(preset_id):
        raise HTTPException(status_code=400, detail="Invalid preset ID")
    
    # Check if preset exists and belongs to user
    existing_preset = await expense_preset_repository.find_one_by_filter({
        "_id": ObjectId(preset_id), 
        "user_id": str(current_user["_id"])
    })
    
    if not existing_preset:
        raise HTTPException(status_code=404, detail="Expense preset not found")
    
    await expense_preset_repository.delete_by_id(preset_id)
    
    return {"message": "Expense preset deleted successfully"}

@router.post("/{preset_id}/use", response_model=dict)
async def use_expense_preset(
    preset_id: str,
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(preset_id):
        raise HTTPException(status_code=400, detail="Invalid preset ID")
    
    preset = await expense_preset_repository.find_one_by_filter({
        "_id": ObjectId(preset_id),
        "user_id": str(current_user["_id"])
    })
    
    if not preset:
        raise HTTPException(status_code=404, detail="Expense preset not found")
    
    if not preset.get("is_active", True):
        raise HTTPException(status_code=400, detail="Expense preset is not active")
    
    account = await account_repository.find_one_by_filter({
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
    
    transaction_id = await transaction_repository.create(transaction_dict)
    
    new_balance = account["balance"] - preset["amount"]
    await account_repository.update_by_id(preset["account_id"], {
        "balance": new_balance, 
        "updated_at": datetime.utcnow()
    })
    
    created_transaction = await transaction_repository.find_by_id(transaction_id)
    created_transaction["id"] = str(created_transaction["_id"])
    created_transaction.pop("_id")
    
    return {
        "message": "Expense registered successfully from preset",
        "transaction": created_transaction
    }