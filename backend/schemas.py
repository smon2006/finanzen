import re
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List

class ExpenseBase(BaseModel):
    amount: float
    category: str
    description: Optional[str] = None
    date: Optional[datetime] = None 

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseOut(ExpenseBase):
    id: int
    user_id: int
    budget_period_id: Optional[int] = None 

    class Config:
        from_attributes = True
class BudgetPeriodBase(BaseModel):
    base_budget: float
    budget_period: str
    custom_days: Optional[int] = None

class BudgetPeriodCreate(BudgetPeriodBase):
    pass

class BudgetPeriodOut(BudgetPeriodBase):
    id: int
    user_id: int
    added_funds: float
    start_date: datetime
    end_date: Optional[datetime] = None
    status: str

    class Config:
        from_attributes = True

class UserSignUp(BaseModel):
    name: str
    email: EmailStr
    
    username: str = Field(
        ..., 
        min_length=5, 
        max_length=15, 
        pattern="^[a-zA-Z0-9]+$",
        description="Must be 5-15 alphanumeric characters."
    )
    
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

class UserOut(BaseModel):
    id: int
    username: str
    name: str
    savings_reserve: float 

    class Config:
        from_attributes = True