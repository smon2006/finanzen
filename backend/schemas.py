import re
from pydantic import BaseModel, EmailStr, Field,field_validator
from typing import Optional, List

# Base properties for an expense
class ExpenseBase(BaseModel):
    amount: float
    category: str
    description: Optional[str] = None
    date: str

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseOut(ExpenseBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class UserSignUp(BaseModel):
    name: str
    email: EmailStr
    
    # Username Rules: 5-15 chars, letters & numbers only
    username: str = Field(
        ..., 
        min_length=5, 
        max_length=15, 
        pattern="^[a-zA-Z0-9]+$",
        description="Must be 5-15 alphanumeric characters."
    )
    
    #Password Rules: Min 8 chars, 1 Upper, 1 Lower, 1 Number, 1 Special
    password: str  

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long.')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter.')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter.')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit.')
        if not re.search(r'[@$!%*?&]', v):
            raise ValueError('Password must contain at least one special character (@$!%*?&).')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class BudgetUpdate(BaseModel):
    budget: float
    budget_period: str
    custom_days: Optional[int] = None

class UserOut(BaseModel):
    name: str
    username: str
    budget: float
    budget_period: str
    custom_days: Optional[int] = None