from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone

def get_utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    
    savings_reserve = Column(Float, default=0.0)

    budgets = relationship("BudgetPeriod", back_populates="owner", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="owner", cascade="all, delete-orphan")


class BudgetPeriod(Base):
    __tablename__ = "budget_periods"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    base_budget = Column(Float, default=0.0)
    added_funds = Column(Float, default=0.0)         
    budget_period = Column(String, default="Monthly") 
    custom_days = Column(Integer, nullable=True)     
    
    start_date = Column(DateTime(timezone=True), nullable=False, default=get_utc_now)
    end_date = Column(DateTime(timezone=True), nullable=True)        
    status = Column(String, default="ACTIVE")         
    
    owner = relationship("User", back_populates="budgets")
    expenses = relationship("Expense", back_populates="budget_period")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    budget_period_id = Column(Integer, ForeignKey("budget_periods.id", ondelete="SET NULL"), nullable=True)
    
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    date = Column(DateTime(timezone=True), nullable=False, default=get_utc_now) 

    owner = relationship("User", back_populates="expenses")
    budget_period = relationship("BudgetPeriod", back_populates="expenses")