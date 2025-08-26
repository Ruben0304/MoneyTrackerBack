from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from models import Account, AccountCreate, AccountUpdate
from database import accounts_collection
from auth import get_current_active_user
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/accounts", tags=["accounts"])

def account_helper(account) -> dict:
    return {
        "id": str(account["_id"]),
        "user_id": account["user_id"],
        "name": account["name"],
        "type": account["type"],
        "balance": account["balance"],
        "currency": account["currency"],
        "created_at": account["created_at"],
        "updated_at": account["updated_at"]
    }

@router.post("/", response_model=dict)
async def create_account(account: AccountCreate, current_user: dict = Depends(get_current_active_user)):
    account_dict = {
        "user_id": str(current_user["_id"]),
        "name": account.name,
        "type": account.type,
        "balance": account.initial_balance,
        "currency": account.currency,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = accounts_collection.insert_one(account_dict)
    new_account = accounts_collection.find_one({"_id": result.inserted_id})
    return account_helper(new_account)

@router.get("/", response_model=List[dict])
async def get_user_accounts(current_user: dict = Depends(get_current_active_user)):
    """Get all accounts for the authenticated user"""
    user_id = str(current_user["_id"])
    accounts = []
    for account in accounts_collection.find({"user_id": user_id}):
        accounts.append(account_helper(account))
    return accounts

@router.get("/{account_id}")
async def get_account(account_id: str, current_user: dict = Depends(get_current_active_user)):
    if not ObjectId.is_valid(account_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid account ID"
        )
    
    account = accounts_collection.find_one({"_id": ObjectId(account_id), "user_id": str(current_user["_id"])})
    if account:
        return account_helper(account)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Account not found"
    )

@router.put("/{account_id}")
async def update_account(account_id: str, account_update: AccountUpdate, current_user: dict = Depends(get_current_active_user)):
    if not ObjectId.is_valid(account_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid account ID"
        )
    
    update_data = account_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    result = accounts_collection.update_one(
        {"_id": ObjectId(account_id), "user_id": str(current_user["_id"])}, 
        {"$set": update_data}
    )
    
    if result.modified_count == 1:
        updated_account = accounts_collection.find_one({"_id": ObjectId(account_id)})
        return account_helper(updated_account)
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Account not found"
    )

@router.delete("/{account_id}")
async def delete_account(account_id: str, current_user: dict = Depends(get_current_active_user)):
    if not ObjectId.is_valid(account_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid account ID"
        )
    
    result = accounts_collection.delete_one({"_id": ObjectId(account_id), "user_id": str(current_user["_id"])})
    if result.deleted_count == 1:
        return {"message": "Account deleted successfully"}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Account not found"
    )