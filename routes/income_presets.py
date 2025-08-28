from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from bson import ObjectId
from datetime import datetime

from models import (
    IncomePreset, IncomePresetCreate, IncomePresetUpdate,
    TransactionCreate, Transaction
)
from database import (
    income_presets_collection, transactions_collection, 
    accounts_collection, auto_savings_collection
)
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
    
    result = income_presets_collection.insert_one(income_preset_dict)
    
    created_preset = income_presets_collection.find_one({"_id": result.inserted_id})
    created_preset["id"] = str(created_preset["_id"])
    created_preset.pop("_id")
    
    return {"message": "Income preset created successfully", "data": created_preset}

@router.get("/", response_model=dict)
async def get_income_presets(current_user: dict = Depends(get_current_user)):
    presets = list(income_presets_collection.find({"user_id": str(current_user["_id"])}))
    
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
    
    preset = income_presets_collection.find_one({
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
    
    result = income_presets_collection.update_one(
        {"_id": ObjectId(preset_id), "user_id": str(current_user["_id"])},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Income preset not found")
    
    return {"message": "Income preset updated successfully"}

@router.delete("/{preset_id}", response_model=dict)
async def delete_income_preset(
    preset_id: str,
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(preset_id):
        raise HTTPException(status_code=400, detail="Invalid preset ID")
    
    result = income_presets_collection.delete_one({
        "_id": ObjectId(preset_id),
        "user_id": str(current_user["_id"])
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Income preset not found")
    
    return {"message": "Income preset deleted successfully"}

@router.post("/{preset_id}/use", response_model=dict)
async def use_income_preset(
    preset_id: str,
    current_user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(preset_id):
        raise HTTPException(status_code=400, detail="Invalid preset ID")
    
    preset = income_presets_collection.find_one({
        "_id": ObjectId(preset_id),
        "user_id": str(current_user["_id"])
    })
    
    if not preset:
        raise HTTPException(status_code=404, detail="Income preset not found")
    
    if not preset.get("is_active", True):
        raise HTTPException(status_code=400, detail="Income preset is not active")
    
    account = accounts_collection.find_one({
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
    
    result = transactions_collection.insert_one(transaction_dict)
    
    new_balance = account["balance"] + preset["amount"]
    accounts_collection.update_one(
        {"_id": ObjectId(preset["account_id"])},
        {"$set": {"balance": new_balance, "updated_at": datetime.utcnow()}}
    )
    
    created_transaction = transactions_collection.find_one({"_id": result.inserted_id})
    created_transaction["id"] = str(created_transaction["_id"])
    created_transaction.pop("_id")
    
    auto_savings_settings = auto_savings_collection.find_one({
        "user_id": str(current_user["_id"]),
        "is_active": True
    })
    
    savings_transaction = None
    if auto_savings_settings:
        savings_amount = preset["amount"] * (auto_savings_settings["percentage"] / 100)
        
        savings_account = accounts_collection.find_one({
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
                
                savings_result = transactions_collection.insert_one(savings_transaction_data)
                
                accounts_collection.update_one(
                    {"_id": ObjectId(preset["account_id"])},
                    {"$set": {"balance": new_balance - savings_amount, "updated_at": datetime.utcnow()}}
                )
                
                accounts_collection.update_one(
                    {"_id": ObjectId(auto_savings_settings["savings_account_id"])},
                    {"$set": {"balance": savings_account["balance"] + savings_amount, "updated_at": datetime.utcnow()}}
                )
                
                savings_transaction = transactions_collection.find_one({"_id": savings_result.inserted_id})
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