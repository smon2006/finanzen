from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional
import jwt
import bcrypt
import os
import models
import schemas
from database import engine, get_db

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_local_key_for_testing")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FINANZEN Core Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BudgetUpdate(BaseModel):
    budget: float
    budget_period: str
    custom_days: Optional[int] = None

class ExpenseCreate(BaseModel):
    amount: float
    category: str
    description: Optional[str] = None



def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_bytes, hashed_bytes)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
    except Exception:
        raise HTTPException(status_code=401, detail="Token has expired or is invalid")
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user



@app.post("/api/signup", status_code=status.HTTP_201_CREATED)
def sign_up(user_data: schemas.UserSignUp, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    db_email = db.query(models.User).filter(models.User.email == user_data.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user_data.password)
    
    new_user = models.User(
        name=user_data.name,
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    token = create_access_token(data={"sub": new_user.username})
    return {"access_token": token, "token_type": "bearer", "name": new_user.name}


@app.post("/api/login")
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == credentials.username).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "name": user.name}



@app.get("/api/dashboard")
def get_dashboard(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    expenses = db.query(models.Expense).filter(models.Expense.user_id == current_user.id).all()
    
    expenses_list = [
        {
            "id": exp.id,
            "amount": exp.amount,
            "category": exp.category,
            "description": exp.description,
            "date": exp.date.strftime("%Y-%m-%d") if hasattr(exp.date, 'strftime') else (str(exp.date)[:10] if exp.date else "")
        }
        for exp in expenses
    ]

    budget = current_user.budget or 0
    total_spent = sum(exp.amount for exp in expenses)
    period = current_user.budget_period or "monthly"
    
    savings = 0
    rollover_deficit = 0
    rollover_message = ""

    if total_spent > budget:
        savings = 0
        rollover_deficit = total_spent - budget
        
        if period == "weekly":
            next_cycle = "next week's"
        elif period == "monthly":
            next_cycle = "next month's"
        elif period == "yearly":
            next_cycle = "next year's"
        elif period == "custom":
            days = current_user.custom_days or 0
            next_cycle = f"your next {days}-day cycle"
        else:
            next_cycle = "your next"
            
        rollover_message = f"Over budget! ₹{rollover_deficit} will be auto-deducted from {next_cycle} budget."
    else:
        savings = budget - total_spent

    return {
        "name": current_user.name,
        "budget": budget,
        "budgetPeriod": period,
        "customDays": current_user.custom_days,
        "expenses": expenses_list,
        "savings": savings,
        "rolloverDeficit": rollover_deficit,
        "rolloverMessage": rollover_message
    }

@app.post("/api/budget")
def set_budget(budget_data: BudgetUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.budget = budget_data.budget
    current_user.budget_period = budget_data.budget_period
    current_user.custom_days = budget_data.custom_days
    
    db.commit()
    return {"message": "Budget updated successfully"}


@app.post("/api/expenses")
def add_expense(expense_data: ExpenseCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_expense = models.Expense(
        amount=expense_data.amount,
        category=expense_data.category,
        description=expense_data.description,
        user_id=current_user.id,
        date=datetime.utcnow() 
    )
    
    db.add(new_expense)
    db.commit()
    return {"message": "Expense added successfully"}


@app.post("/api/budget/reset")
def reset_budget(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.budget = 0
    current_user.budget_period = 'monthly'
    current_user.custom_days = None
    db.query(models.Expense).filter(models.Expense.user_id == current_user.id).delete()
    
    db.commit()
    return {"message": "Budget and expenses wiped clean"}