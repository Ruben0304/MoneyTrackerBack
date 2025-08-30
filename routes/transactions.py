from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from models import Transaction, TransactionCreate
from repositories.transaction_repository import transaction_repository
from repositories.account_repository import account_repository
from auth import get_current_active_user
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/transactions", tags=["transactions"])

def transaction_helper(transaction) -> dict:
    return {
        "id": str(transaction["_id"]),
        "user_id": transaction["user_id"],
        "account_id": transaction["account_id"],
        "amount": transaction["amount"],
        "type": transaction["type"],
        "category": transaction["category"],
        "description": transaction["description"],
        "date": transaction["date"],
        "currency": transaction["currency"],
        "transfer_to_account_id": transaction.get("transfer_to_account_id")
    }

async def update_account_balance(account_id: str, amount: float, operation: str):
    """Update account balance based on transaction type"""
    if operation == "add":
        await account_repository.increment_balance(account_id, amount)
        await account_repository.update_by_id(account_id, {"updated_at": datetime.utcnow()})
    elif operation == "subtract":
        await account_repository.increment_balance(account_id, -amount)
        await account_repository.update_by_id(account_id, {"updated_at": datetime.utcnow()})

@router.post("/", response_model=dict)
async def create_transaction(transaction: TransactionCreate, current_user: dict = Depends(get_current_active_user)):
    # Verify account exists and belongs to user
    user_id = str(current_user["_id"])
    account = await account_repository.find_one_by_filter({"_id": ObjectId(transaction.account_id), "user_id": user_id})
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found or doesn't belong to user"
        )
    
    transaction_dict = {
        "user_id": user_id,
        "account_id": transaction.account_id,
        "amount": transaction.amount,
        "type": transaction.type,
        "category": transaction.category,
        "description": transaction.description,
        "date": datetime.utcnow(),
        "currency": account["currency"],
        "transfer_to_account_id": transaction.transfer_to_account_id
    }
    
    # Handle different transaction types
    if transaction.type == "income":
        await update_account_balance(transaction.account_id, transaction.amount, "add")
        
        # Handle auto-savings for income transactions
        if (transaction.auto_savings_percentage is not None and 
            transaction.auto_savings_account_id is not None and
            transaction.auto_savings_percentage > 0):
            
            # Validate savings account exists and belongs to user
            savings_account = await account_repository.find_one_by_filter({
                "_id": ObjectId(transaction.auto_savings_account_id), 
                "user_id": user_id
            })
            if not savings_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Savings account not found or doesn't belong to user"
                )
            
            # Calculate savings amount
            savings_amount = transaction.amount * (transaction.auto_savings_percentage / 100)
            
            # Check if there's enough balance in the income account after the income
            income_account_new_balance = account["balance"] + transaction.amount
            if income_account_new_balance < savings_amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient balance for auto-savings transfer"
                )
            
            # Verify accounts have the same currency
            if account["currency"] != savings_account["currency"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot transfer auto-savings between different currencies"
                )
            
            # Transfer the savings amount
            await update_account_balance(transaction.account_id, savings_amount, "subtract")
            await update_account_balance(transaction.auto_savings_account_id, savings_amount, "add")
            
            # Create a separate transaction record for the auto-savings transfer
            auto_savings_transaction = {
                "user_id": user_id,
                "account_id": transaction.account_id,
                "amount": savings_amount,
                "type": "transfer",
                "category": "Auto Savings",
                "description": f"Auto savings ({transaction.auto_savings_percentage}%) from: {transaction.description}",
                "date": datetime.utcnow(),
                "currency": account["currency"],
                "transfer_to_account_id": transaction.auto_savings_account_id
            }
            await transaction_repository.create(auto_savings_transaction)
    elif transaction.type == "expense":
        if account["balance"] < transaction.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient balance"
            )
        await update_account_balance(transaction.account_id, transaction.amount, "subtract")
    elif transaction.type == "transfer":
        if not transaction.transfer_to_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer destination account is required"
            )
        
        to_account = await account_repository.find_one_by_filter({
            "_id": ObjectId(transaction.transfer_to_account_id), 
            "user_id": user_id
        })
        if not to_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Destination account not found"
            )
        
        if account["currency"] != to_account["currency"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot transfer between different currencies"
            )
        
        if account["balance"] < transaction.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient balance"
            )
        
        await update_account_balance(transaction.account_id, transaction.amount, "subtract")
        await update_account_balance(transaction.transfer_to_account_id, transaction.amount, "add")
    
    transaction_id = await transaction_repository.create(transaction_dict)
    new_transaction = await transaction_repository.find_by_id(transaction_id)
    return transaction_helper(new_transaction)

@router.get("/", response_model=List[dict])
async def get_user_transactions(current_user: dict = Depends(get_current_active_user), limit: Optional[int] = 50, offset: Optional[int] = 0):
    """Get all transactions for the authenticated user"""
    user_id = str(current_user["_id"])
    # Use direct collection query with pagination
    transactions = list(transaction_repository.collection.find({"user_id": user_id}).sort("date", -1).skip(offset).limit(limit))
    return [transaction_helper(transaction) for transaction in transactions]

@router.get("/account/{account_id}", response_model=List[dict])
async def get_account_transactions(account_id: str, current_user: dict = Depends(get_current_active_user), limit: Optional[int] = 50):
    """Get transactions for a specific account (must belong to authenticated user)"""
    # Verify account belongs to user
    account = await account_repository.find_one_by_filter({"_id": ObjectId(account_id), "user_id": str(current_user["_id"])})
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Use direct collection query with pagination
    transactions = list(transaction_repository.collection.find({"account_id": account_id, "user_id": str(current_user["_id"])}).sort("date", -1).limit(limit))
    return [transaction_helper(transaction) for transaction in transactions]

@router.get("/{transaction_id}")
async def get_transaction(transaction_id: str, current_user: dict = Depends(get_current_active_user)):
    if not ObjectId.is_valid(transaction_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transaction ID"
        )
    
    transaction = await transaction_repository.find_one_by_filter({"_id": ObjectId(transaction_id), "user_id": str(current_user["_id"])})
    if transaction:
        return transaction_helper(transaction)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Transaction not found"
    )

@router.delete("/{transaction_id}")
async def delete_transaction(transaction_id: str, current_user: dict = Depends(get_current_active_user)):
    if not ObjectId.is_valid(transaction_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transaction ID"
        )
    
    # Get transaction to reverse balance changes
    user_id = str(current_user["_id"])
    transaction = await transaction_repository.find_one_by_filter({"_id": ObjectId(transaction_id), "user_id": user_id})
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Reverse the balance changes
    if transaction["type"] == "income":
        await update_account_balance(transaction["account_id"], transaction["amount"], "subtract")
    elif transaction["type"] == "expense":
        await update_account_balance(transaction["account_id"], transaction["amount"], "add")
    elif transaction["type"] == "transfer":
        await update_account_balance(transaction["account_id"], transaction["amount"], "add")
        if transaction.get("transfer_to_account_id"):
            await update_account_balance(transaction["transfer_to_account_id"], transaction["amount"], "subtract")
    
    success = await transaction_repository.delete_by_id(transaction_id)
    if success:
        return {"message": "Transaction deleted successfully"}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Transaction not found"
    )