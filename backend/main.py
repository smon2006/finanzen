from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
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
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def calculate_horizon_end_date(start_date: datetime, period: str, custom_days: Optional[int] = None) -> datetime:
    period_lower = period.lower()
    if period_lower == "weekly":
        return start_date + timedelta(weeks=1)
    elif period_lower == "monthly":
        return start_date + timedelta(days=30)  
    elif period_lower == "yearly":
        return start_date + timedelta(days=365)
    elif period_lower == "custom" and custom_days:
        return start_date + timedelta(days=custom_days)
    return start_date + timedelta(days=30)

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
        password_hash=hashed_password,
        savings_reserve=0.0
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
    active_budget = db.query(models.BudgetPeriod).filter(
        models.BudgetPeriod.user_id == current_user.id,
        models.BudgetPeriod.status == "ACTIVE"
    ).first()
    
    if active_budget:
        expenses = db.query(models.Expense).filter(models.Expense.budget_period_id == active_budget.id).all()
        budget = active_budget.base_budget
        period = active_budget.budget_period or "monthly"
        custom_days = active_budget.custom_days
        has_active_budget = True 
    else:
        expenses = db.query(models.Expense).filter(models.Expense.user_id == current_user.id, models.Expense.budget_period_id == None).all()
        budget = 0.0
        period = "none"           
        custom_days = None
        has_active_budget = False 
    
    expenses_list = [
        {
            "id": exp.id,
            "amount": exp.amount,
            "category": exp.category,
            "description": exp.description,
            "date": exp.date.strftime("%Y-%m-%d") if exp.date else ""
        }
        for exp in expenses
    ]

    total_spent = sum(exp.amount for exp in expenses)
    savings = 0.0
    rollover_deficit = 0.0
    rollover_message = ""

    if total_spent > budget:
        if has_active_budget:  
            rollover_deficit = total_spent - budget
            period_lower = period.lower()
            if period_lower == "weekly":
                next_cycle = "next week's"
            elif period_lower == "monthly":
                next_cycle = "next month's"
            elif period_lower == "yearly":
                next_cycle = "next year's"
            elif period_lower == "custom":
                days = custom_days or 0
                next_cycle = f"your next {days}-day cycle"
            else:
                next_cycle = "your next"
            rollover_message = f"Over budget! ₹{rollover_deficit:.2f} will be auto-deducted from {next_cycle} budget."
    else:
        savings = budget - total_spent

    return {
        "name": current_user.name,
        "hasActiveBudget": has_active_budget,
        "budget": budget,
        "budgetPeriod": period,    
        "budget_period": period,      
        "period_type": period,
        "customDays": custom_days,
        "custom_days": custom_days,
        "expenses": expenses_list,
        "savings": savings,
        "rolloverDeficit": rollover_deficit,
        "rolloverMessage": rollover_message,
        "savingsReserve": current_user.savings_reserve
    }

@app.post("/api/budget")
def set_budget(budget_data: schemas.BudgetPeriodCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    active_budget = db.query(models.BudgetPeriod).filter(
        models.BudgetPeriod.user_id == current_user.id,
        models.BudgetPeriod.status == "ACTIVE"
    ).first()
    
    now = datetime.now(timezone.utc)
    end_date = calculate_horizon_end_date(now, budget_data.budget_period, budget_data.custom_days)
    
    last_archived = db.query(models.BudgetPeriod).filter(
        models.BudgetPeriod.user_id == current_user.id,
        models.BudgetPeriod.status == "ARCHIVED"
    ).order_by(models.BudgetPeriod.id.desc()).first()
    
    deficit_deduction = 0.0
    if last_archived:
        archived_expenses = db.query(models.Expense).filter(models.Expense.budget_period_id == last_archived.id).all()
        archived_spent = sum(exp.amount for exp in archived_expenses)
        if archived_spent > last_archived.base_budget:
            deficit_deduction = archived_spent - last_archived.base_budget
            
    final_starting_budget = max(0.0, budget_data.base_budget - deficit_deduction)
    
    if active_budget:
        active_budget.base_budget = final_starting_budget
        active_budget.budget_period = budget_data.budget_period
        active_budget.custom_days = budget_data.custom_days
        active_budget.end_date = end_date
    else:
        active_budget = models.BudgetPeriod(
            user_id=current_user.id,
            base_budget=final_starting_budget,
            budget_period=budget_data.budget_period,
            custom_days=budget_data.custom_days,
            start_date=now,
            end_date=end_date,
            status="ACTIVE"
        )
        db.add(active_budget)
    
    db.commit()
    return {"message": "Budget updated successfully"}


@app.post("/api/expenses")
def add_expense(expense_data: schemas.ExpenseCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    active_budget = db.query(models.BudgetPeriod).filter(
        models.BudgetPeriod.user_id == current_user.id,
        models.BudgetPeriod.status == "ACTIVE"
    ).first()
    
    bp_id = active_budget.id if active_budget else None
    
    new_expense = models.Expense(
        amount=expense_data.amount,
        category=expense_data.category,
        description=expense_data.description,
        user_id=current_user.id,
        budget_period_id=bp_id,
        date=datetime.now(timezone.utc)
    )
    
    db.add(new_expense)
    db.commit()
    return {"message": "Expense added successfully"}


@app.post("/api/budget/reset")
def reset_budget(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    active_budget = db.query(models.BudgetPeriod).filter(
        models.BudgetPeriod.user_id == current_user.id,
        models.BudgetPeriod.status == "ACTIVE"
    ).first()
    
    if not active_budget:
        raise HTTPException(status_code=400, detail="No active budget cycle found to reset.")
        
    expenses = db.query(models.Expense).filter(models.Expense.budget_period_id == active_budget.id).all()
    total_spent = sum(exp.amount for exp in expenses)
    budget = active_budget.base_budget
    
    if total_spent < budget:
        surplus = budget - total_spent
        current_user.savings_reserve += surplus
    
    active_budget.status = "ARCHIVED"
    active_budget.end_date = datetime.now(timezone.utc)
    
    db.commit()
    return {"message": "Budget cycle successfully archived clean", "hasActiveBudget": False}
@app.get("/api/history")
def get_expense_history(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    archived_periods = db.query(models.BudgetPeriod).filter(
        models.BudgetPeriod.user_id == current_user.id,
        models.BudgetPeriod.status == "ARCHIVED"
    ).order_by(models.BudgetPeriod.end_date.desc()).all()
    
    sessions_list = []
    for period in archived_periods:
        period_expenses = db.query(models.Expense).filter(models.Expense.budget_period_id == period.id).all()
        total_spent = sum(exp.amount for exp in period_expenses)
        
        sessions_list.append({
            "id": period.id,
            "start_date": period.start_date.strftime("%Y-%m-%d") if period.start_date else "",
            "end_date": period.end_date.strftime("%Y-%m-%d") if period.end_date else "Now",
            "period_type": period.budget_period,
            "starting_budget": period.base_budget,
            "total_spent": total_spent,
            "expenses": [
                {
                    "amount": exp.amount,
                    "category": exp.category,
                    "description": exp.description,
                    "date": exp.date.strftime("%Y-%m-%d") if exp.date else ""
                } for exp in period_expenses
            ]
        })
        
    return {
        "name": current_user.name,
        "total_archived_sessions": len(sessions_list),
        "sessions": sessions_list
    }