from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from bson import ObjectId
from .base import PyObjectId

class IncomePreset(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    name: str
    amount: float
    category: str
    description: Optional[str] = None
    collect_day: Optional[int] = None
    currency: Literal["USD", "CUP"]
    account_id: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class IncomePresetCreate(BaseModel):
    name: str
    amount: float
    category: str
    description: Optional[str] = None
    collect_day: Optional[int] = None
    currency: Literal["USD", "CUP"]
    account_id: str

class IncomePresetUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    collect_day: Optional[int] = None
    account_id: Optional[str] = None
    is_active: Optional[bool] = None