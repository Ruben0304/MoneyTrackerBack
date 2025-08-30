from pydantic import BaseModel, Field
from typing import Optional, Literal
from bson import ObjectId
from .base import PyObjectId

class Category(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str
    icon: str
    color: str
    type: Literal["income", "expense"]

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}