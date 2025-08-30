from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from bson import ObjectId
from .base import PyObjectId

class Budget(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    name: str
    target_amount: float
    current_amount: float = 0.0
    currency: Literal["USD", "CUP"]
    source_account_id: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_completed: bool = False

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class BudgetCreate(BaseModel):
    name: str
    target_amount: float
    currency: Literal["USD", "CUP"]
    source_account_id: str
    description: Optional[str] = None

class BudgetUpdate(BaseModel):
    name: Optional[str] = None
    target_amount: Optional[float] = None
    current_amount: Optional[float] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None