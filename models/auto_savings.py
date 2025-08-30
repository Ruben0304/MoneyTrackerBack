from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId
from .base import PyObjectId

class AutoSavings(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    percentage: float = 30.0
    savings_account_id: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class AutoSavingsCreate(BaseModel):
    percentage: float = 30.0
    savings_account_id: str

class AutoSavingsUpdate(BaseModel):
    percentage: Optional[float] = None
    savings_account_id: Optional[str] = None
    is_active: Optional[bool] = None