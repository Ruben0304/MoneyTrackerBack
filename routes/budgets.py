from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from models import Budget, BudgetCreate, BudgetUpdate
from repositories.budget_repository import budget_repository
from repositories.account_repository import account_repository
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
    account = await account_repository.find_one_by_filter({"_id": ObjectId(budget.source_account_id), "user_id": user_id})
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
    
    budget_id = await budget_repository.create(budget_dict)
    new_budget = await budget_repository.find_by_id(budget_id)
    return budget_helper(new_budget)

@router.get("/", response_model=List[dict])
async def get_user_budgets(current_user: dict = Depends(get_current_active_user)):
    """Get all budgets for the authenticated user"""
    user_id = str(current_user["_id"])
    budgets = await budget_repository.find_by_user_id(user_id)
    return [budget_helper(budget) for budget in budgets]

@router.get("/{budget_id}")
async def get_budget(budget_id: str, current_user: dict = Depends(get_current_active_user)):
    if not ObjectId.is_valid(budget_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid budget ID"
        )
    
    budget = await budget_repository.find_one_by_filter({"_id": ObjectId(budget_id), "user_id": str(current_user["_id"])})
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
    existing_budget = await budget_repository.find_one_by_filter({"_id": ObjectId(budget_id), "user_id": user_id})
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
    
    success = await budget_repository.update_by_id(budget_id, update_data)
    
    if success:
        updated_budget = await budget_repository.find_by_id(budget_id)
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
    budget = await budget_repository.find_one_by_filter({"_id": ObjectId(budget_id), "user_id": user_id})
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found or doesn't belong to user"
        )
    
    # Verify source account has sufficient balance
    account = await account_repository.find_by_id(budget["source_account_id"])
    if account["balance"] < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance in source account"
        )
    
    # Update account balance and budget amount
    new_current_amount = budget["current_amount"] + amount
    is_completed = new_current_amount >= budget["target_amount"]
    
    await account_repository.increment_balance(budget["source_account_id"], -amount)
    await account_repository.update_by_id(budget["source_account_id"], {"updated_at": datetime.utcnow()})
    
    await budget_repository.update_by_id(budget_id, {
        "current_amount": new_current_amount,
        "is_completed": is_completed,
        "updated_at": datetime.utcnow()
    })
    
    updated_budget = await budget_repository.find_by_id(budget_id)
    return budget_helper(updated_budget)

@router.delete("/{budget_id}")
async def delete_budget(budget_id: str, current_user: dict = Depends(get_current_active_user)):
    if not ObjectId.is_valid(budget_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid budget ID"
        )
    
    # Verify budget belongs to user before deleting
    user_id = str(current_user["_id"])
    existing_budget = await budget_repository.find_one_by_filter({"_id": ObjectId(budget_id), "user_id": user_id})
    if not existing_budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    success = await budget_repository.delete_by_id(budget_id)
    if success:
        return {"message": "Budget deleted successfully"}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Budget not found"
    )