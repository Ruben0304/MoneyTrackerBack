from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from bson import ObjectId
from .base import PyObjectId

class Account(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    name: str
    type: Literal["billetera", "tarjeta", "ahorro"]
    balance: float
    currency: Literal["USD", "CUP"]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class AccountCreate(BaseModel):
    name: str
    type: Literal["billetera", "tarjeta", "ahorro"]
    currency: Literal["USD", "CUP"]
    initial_balance: float = 0.0

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    balance: Optional[float] = None