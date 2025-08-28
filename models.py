from pydantic import BaseModel, Field
from pydantic_core import core_schema
from typing import Optional, Literal, Any
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(ObjectId),
                    core_schema.chain_schema(
                        [
                            core_schema.str_schema(),
                            core_schema.no_info_plain_validator_function(cls.validate),
                        ]
                    ),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid objectid")

class User(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str
    email: str
    password_hash: str
    role: Literal["basic", "pro", "max"] = "basic"
    is_active: bool = True
    ai_requests_limit: int = 10  # basic: 10, pro: 100, max: unlimited (-1)
    ai_requests_used: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

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

# Request models for API endpoints
class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[Literal["basic", "pro", "max"]] = "basic"

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[Literal["basic", "pro", "max"]] = None
    is_active: Optional[bool] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: dict

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class AccountCreate(BaseModel):
    name: str
    type: Literal["billetera", "tarjeta", "ahorro"]
    currency: Literal["USD", "CUP"]
    initial_balance: float = 0.0

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    balance: Optional[float] = None

class TransactionCreate(BaseModel):
    account_id: str
    amount: float
    type: Literal["income", "expense", "transfer"]
    category: str
    description: str
    transfer_to_account_id: Optional[str] = None

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

class ExpensePreset(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    name: str
    amount: float
    category: str
    description: Optional[str] = None
    due_day: Optional[int] = None
    currency: Literal["USD", "CUP"]
    account_id: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

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

class IncomePresetCreate(BaseModel):
    name: str
    amount: float
    category: str
    description: Optional[str] = None
    collect_day: Optional[int] = None
    currency: Literal["USD", "CUP"]
    account_id: str

class ExpensePresetCreate(BaseModel):
    name: str
    amount: float
    category: str
    description: Optional[str] = None
    due_day: Optional[int] = None
    currency: Literal["USD", "CUP"]
    account_id: str

class AutoSavingsCreate(BaseModel):
    percentage: float = 30.0
    savings_account_id: str

class IncomePresetUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    collect_day: Optional[int] = None
    account_id: Optional[str] = None
    is_active: Optional[bool] = None

class ExpensePresetUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    due_day: Optional[int] = None
    account_id: Optional[str] = None
    is_active: Optional[bool] = None

class AutoSavingsUpdate(BaseModel):
    percentage: Optional[float] = None
    savings_account_id: Optional[str] = None
    is_active: Optional[bool] = None