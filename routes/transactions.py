from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from models import Transaction, TransactionCreate
from database import transactions_collection, accounts_collection
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
        accounts_collection.update_one(
            {"_id": ObjectId(account_id)},
            {"$inc": {"balance": amount}, "$set": {"updated_at": datetime.utcnow()}}
        )
    elif operation == "subtract":
        accounts_collection.update_one(
            {"_id": ObjectId(account_id)},
            {"$inc": {"balance": -amount}, "$set": {"updated_at": datetime.utcnow()}}
        )

@router.post("/", response_model=dict)
async def create_transaction(transaction: TransactionCreate, current_user: dict = Depends(get_current_active_user)):
    # Verify account exists and belongs to user
    user_id = str(current_user["_id"])
    account = accounts_collection.find_one({"_id": ObjectId(transaction.account_id), "user_id": user_id})
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
        
        to_account = accounts_collection.find_one({
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
    
    result = transactions_collection.insert_one(transaction_dict)
    new_transaction = transactions_collection.find_one({"_id": result.inserted_id})
    return transaction_helper(new_transaction)

@router.get("/", response_model=List[dict])
async def get_user_transactions(current_user: dict = Depends(get_current_active_user), limit: Optional[int] = 50, offset: Optional[int] = 0):
    """Get all transactions for the authenticated user"""
    user_id = str(current_user["_id"])
    transactions = []
    cursor = transactions_collection.find({"user_id": user_id}).sort("date", -1).skip(offset).limit(limit)
    for transaction in cursor:
        transactions.append(transaction_helper(transaction))
    return transactions

@router.get("/account/{account_id}", response_model=List[dict])
async def get_account_transactions(account_id: str, current_user: dict = Depends(get_current_active_user), limit: Optional[int] = 50):
    """Get transactions for a specific account (must belong to authenticated user)"""
    # Verify account belongs to user
    account = accounts_collection.find_one({"_id": ObjectId(account_id), "user_id": str(current_user["_id"])})
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    transactions = []
    cursor = transactions_collection.find({"account_id": account_id, "user_id": str(current_user["_id"])}).sort("date", -1).limit(limit)
    for transaction in cursor:
        transactions.append(transaction_helper(transaction))
    return transactions

@router.get("/{transaction_id}")
async def get_transaction(transaction_id: str, current_user: dict = Depends(get_current_active_user)):
    if not ObjectId.is_valid(transaction_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transaction ID"
        )
    
    transaction = transactions_collection.find_one({"_id": ObjectId(transaction_id), "user_id": str(current_user["_id"])})
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
    transaction = transactions_collection.find_one({"_id": ObjectId(transaction_id), "user_id": user_id})
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
    
    result = transactions_collection.delete_one({"_id": ObjectId(transaction_id)})
    if result.deleted_count == 1:
        return {"message": "Transaction deleted successfully"}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Transaction not found"
    )