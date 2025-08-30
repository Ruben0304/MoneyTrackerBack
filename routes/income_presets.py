from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from bson import ObjectId
from datetime import datetime

from models import (
    IncomePreset, IncomePresetCreate, IncomePresetUpdate,
    TransactionCreate, Transaction
)
from repositories.income_preset_repository import income_preset_repository
from repositories.transaction_repository import transaction_repository
from repositories.account_repository import account_repository
from repositories.auto_savings_repository import auto_savings_repository
from auth import get_current_user

router = APIRouter()

@router.post("/", response_model=dict)
async def create_income_preset(
    income_preset: IncomePresetCreate,
    current_user: dict = Depends(get_current_user)
):
    income_preset_dict = income_preset.dict()
    income_preset_dict["user_id"] = str(current_user["_id"])
    income_preset_dict["created_at"] = datetime.utcnow()
    income_preset_dict["updated_at"] = datetime.utcnow()
    
    preset_id = await income_preset_repository.create(income_preset_dict)
    
    created_preset = await income_preset_repository.find_by_id(preset_id)
    created_preset["id"] = str(created_preset["_id"])
    created_preset.pop("_id")
    
    return {"message": "Income preset created successfully", "data": created_preset}

@router.get("/", response_model=dict)
async def get_income_presets(current_user: dict = Depends(get_current_user)):
    presets = await income_preset_repository.find_by_user_id(str(current_user["_id"]))
    
    for preset in presets:
        preset["id"] = str(preset["_id"])
        preset.pop("_id")
    
    return {"data": presets}

@router.get("/{preset_id}", response_model=dict)
async def get_income_preset(
    preset_id: str,
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(preset_id):
        raise HTTPException(status_code=400, detail="Invalid preset ID")
    
    preset = await income_preset_repository.find_one_by_filter({
        "_id": ObjectId(preset_id),
        "user_id": str(current_user["_id"])
    })
    
    if not preset:
        raise HTTPException(status_code=404, detail="Income preset not found")
    
    preset["id"] = str(preset["_id"])
    preset.pop("_id")
    
    return {"data": preset}

@router.put("/{preset_id}", response_model=dict)
async def update_income_preset(
    preset_id: str,
    preset_update: IncomePresetUpdate,
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(preset_id):
        raise HTTPException(status_code=400, detail="Invalid preset ID")
    
    update_data = {k: v for k, v in preset_update.dict(exclude_unset=True).items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    update_data["updated_at"] = datetime.utcnow()
    
    # Check if preset exists and belongs to user
    existing_preset = await income_preset_repository.find_one_by_filter({
        "_id": ObjectId(preset_id), 
        "user_id": str(current_user["_id"])
    })
    
    if not existing_preset:
        raise HTTPException(status_code=404, detail="Income preset not found")
    
    await income_preset_repository.update_by_id(preset_id, update_data)
    
    return {"message": "Income preset updated successfully"}

@router.delete("/{preset_id}", response_model=dict)
async def delete_income_preset(
    preset_id: str,
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(preset_id):
        raise HTTPException(status_code=400, detail="Invalid preset ID")
    
    # Check if preset exists and belongs to user
    existing_preset = await income_preset_repository.find_one_by_filter({
        "_id": ObjectId(preset_id), 
        "user_id": str(current_user["_id"])
    })
    
    if not existing_preset:
        raise HTTPException(status_code=404, detail="Income preset not found")
    
    await income_preset_repository.delete_by_id(preset_id)
    
    return {"message": "Income preset deleted successfully"}

@router.post("/{preset_id}/use", response_model=dict)
async def use_income_preset(
    preset_id: str,
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(preset_id):
        raise HTTPException(status_code=400, detail="Invalid preset ID")
    
    preset = await income_preset_repository.find_one_by_filter({
        "_id": ObjectId(preset_id),
        "user_id": str(current_user["_id"])
    })
    
    if not preset:
        raise HTTPException(status_code=404, detail="Income preset not found")
    
    if not preset.get("is_active", True):
        raise HTTPException(status_code=400, detail="Income preset is not active")
    
    account = await account_repository.find_one_by_filter({
        "_id": ObjectId(preset["account_id"]),
        "user_id": str(current_user["_id"])
    })
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    transaction_data = TransactionCreate(
        account_id=preset["account_id"],
        amount=preset["amount"],
        type="income",
        category=preset["category"],
        description=preset.get("description", preset["name"])
    )
    
    transaction_dict = transaction_data.dict()
    transaction_dict["user_id"] = str(current_user["_id"])
    transaction_dict["date"] = datetime.utcnow()
    transaction_dict["currency"] = preset["currency"]
    
    transaction_id = await transaction_repository.create(transaction_dict)
    
    new_balance = account["balance"] + preset["amount"]
    await account_repository.update_by_id(preset["account_id"], {
        "balance": new_balance, 
        "updated_at": datetime.utcnow()
    })
    
    created_transaction = await transaction_repository.find_by_id(transaction_id)
    created_transaction["id"] = str(created_transaction["_id"])
    created_transaction.pop("_id")
    
    auto_savings_settings = await auto_savings_repository.find_one_by_filter({
        "user_id": str(current_user["_id"]),
        "is_active": True
    })
    
    savings_transaction = None
    if auto_savings_settings:
        savings_amount = preset["amount"] * (auto_savings_settings["percentage"] / 100)
        
        savings_account = await account_repository.find_one_by_filter({
            "_id": ObjectId(auto_savings_settings["savings_account_id"]),
            "user_id": str(current_user["_id"])
        })
        
        if savings_account and savings_account["currency"] == preset["currency"]:
            if new_balance >= savings_amount:
                savings_transaction_data = {
                    "user_id": str(current_user["_id"]),
                    "account_id": preset["account_id"],
                    "amount": savings_amount,
                    "type": "transfer",
                    "category": "ahorro",
                    "description": f"Autoahorro ({auto_savings_settings['percentage']}%) - {preset['name']}",
                    "date": datetime.utcnow(),
                    "currency": preset["currency"],
                    "transfer_to_account_id": auto_savings_settings["savings_account_id"]
                }
                
                savings_transaction_id = await transaction_repository.create(savings_transaction_data)
                
                await account_repository.update_by_id(preset["account_id"], {
                    "balance": new_balance - savings_amount, 
                    "updated_at": datetime.utcnow()
                })
                
                await account_repository.update_by_id(auto_savings_settings["savings_account_id"], {
                    "balance": savings_account["balance"] + savings_amount, 
                    "updated_at": datetime.utcnow()
                })
                
                savings_transaction = await transaction_repository.find_by_id(savings_transaction_id)
                savings_transaction["id"] = str(savings_transaction["_id"])
                savings_transaction.pop("_id")
    
    response_data = {
        "message": "Income registered successfully from preset",
        "transaction": created_transaction
    }
    
    if savings_transaction:
        response_data["auto_savings"] = {
            "percentage": auto_savings_settings["percentage"],
            "amount": savings_amount,
            "transaction": savings_transaction
        }
    
    return response_data