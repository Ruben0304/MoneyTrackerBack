from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from models import Budget, BudgetCreate, BudgetUpdate
from database import budgets_collection, accounts_collection
from auth import get_current_active_user
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/budgets", tags=["budgets"])

def budget_helper(budget) -> dict:
    return {
        "id": str(budget["_id"]),
        "user_id": budget["user_id"],
        "name": budget["name"],
        "target_amount": budget["target_amount"],
        "current_amount": budget["current_amount"],
        "currency": budget["currency"],
        "source_account_id": budget["source_account_id"],
        "description": budget.get("description"),
        "created_at": budget["created_at"],
        "updated_at": budget["updated_at"],
        "is_completed": budget["is_completed"]
    }

@router.post("/", response_model=dict)
async def create_budget(budget: BudgetCreate, current_user: dict = Depends(get_current_active_user)):
    # Verify source account exists and belongs to user
    user_id = str(current_user["_id"])
    account = accounts_collection.find_one({"_id": ObjectId(budget.source_account_id), "user_id": user_id})
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source account not found or doesn't belong to user"
        )
    
    budget_dict = {
        "user_id": user_id,
        "name": budget.name,
        "target_amount": budget.target_amount,
        "current_amount": 0.0,
        "currency": budget.currency,
        "source_account_id": budget.source_account_id,
        "description": budget.description,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_completed": False
    }
    
    result = budgets_collection.insert_one(budget_dict)
    new_budget = budgets_collection.find_one({"_id": result.inserted_id})
    return budget_helper(new_budget)

@router.get("/", response_model=List[dict])
async def get_user_budgets(current_user: dict = Depends(get_current_active_user)):
    """Get all budgets for the authenticated user"""
    user_id = str(current_user["_id"])
    budgets = []
    for budget in budgets_collection.find({"user_id": user_id}):
        budgets.append(budget_helper(budget))
    return budgets

@router.get("/{budget_id}")
async def get_budget(budget_id: str, current_user: dict = Depends(get_current_active_user)):
    if not ObjectId.is_valid(budget_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid budget ID"
        )
    
    budget = budgets_collection.find_one({"_id": ObjectId(budget_id), "user_id": str(current_user["_id"])})
    if budget:
        return budget_helper(budget)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Budget not found"
    )

@router.put("/{budget_id}")
async def update_budget(budget_id: str, budget_update: BudgetUpdate, current_user: dict = Depends(get_current_active_user)):
    if not ObjectId.is_valid(budget_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid budget ID"
        )
    
    # Verify budget belongs to user
    user_id = str(current_user["_id"])
    existing_budget = budgets_collection.find_one({"_id": ObjectId(budget_id), "user_id": user_id})
    if not existing_budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found or doesn't belong to user"
        )
    
    update_data = budget_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    # Check if budget is completed
    if "current_amount" in update_data or "target_amount" in update_data:
        current_amount = update_data.get("current_amount", existing_budget["current_amount"])
        target_amount = update_data.get("target_amount", existing_budget["target_amount"])
        if current_amount >= target_amount:
            update_data["is_completed"] = True
    
    result = budgets_collection.update_one(
        {"_id": ObjectId(budget_id)}, 
        {"$set": update_data}
    )
    
    if result.modified_count == 1:
        updated_budget = budgets_collection.find_one({"_id": ObjectId(budget_id)})
        return budget_helper(updated_budget)
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Budget not found"
    )

@router.post("/{budget_id}/add-funds")
async def add_funds_to_budget(budget_id: str, amount: float, current_user: dict = Depends(get_current_active_user)):
    if not ObjectId.is_valid(budget_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid budget ID"
        )
    
    user_id = str(current_user["_id"])
    budget = budgets_collection.find_one({"_id": ObjectId(budget_id), "user_id": user_id})
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found or doesn't belong to user"
        )
    
    # Verify source account has sufficient balance
    account = accounts_collection.find_one({"_id": ObjectId(budget["source_account_id"])})
    if account["balance"] < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance in source account"
        )
    
    # Update account balance and budget amount
    new_current_amount = budget["current_amount"] + amount
    is_completed = new_current_amount >= budget["target_amount"]
    
    accounts_collection.update_one(
        {"_id": ObjectId(budget["source_account_id"])},
        {"$inc": {"balance": -amount}, "$set": {"updated_at": datetime.utcnow()}}
    )
    
    budgets_collection.update_one(
        {"_id": ObjectId(budget_id)},
        {
            "$set": {
                "current_amount": new_current_amount,
                "is_completed": is_completed,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    updated_budget = budgets_collection.find_one({"_id": ObjectId(budget_id)})
    return budget_helper(updated_budget)

@router.delete("/{budget_id}")
async def delete_budget(budget_id: str, current_user: dict = Depends(get_current_active_user)):
    if not ObjectId.is_valid(budget_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid budget ID"
        )
    
    result = budgets_collection.delete_one({"_id": ObjectId(budget_id), "user_id": str(current_user["_id"])})
    if result.deleted_count == 1:
        return {"message": "Budget deleted successfully"}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Budget not found"
    )