from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from bson import ObjectId
from .base import PyObjectId

class Transaction(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    account_id: str
    amount: float
    type: Literal["income", "expense", "transfer"]
    category: str
    description: str
    date: datetime = Field(default_factory=datetime.utcnow)
    currency: Literal["USD", "CUP"]
    transfer_to_account_id: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class TransactionCreate(BaseModel):
    account_id: str
    amount: float
    type: Literal["income", "expense", "transfer"]
    category: str
    description: str
    transfer_to_account_id: Optional[str] = None
    auto_savings_percentage: Optional[float] = None
    auto_savings_account_id: Optional[str] = None