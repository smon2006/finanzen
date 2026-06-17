from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    budget = Column(Float, default=0.0)
    budget_period = Column(String, default="Monthly")
    custom_days = Column(Integer, nullable=True)     

    expenses = relationship("Expense", back_populates="owner", cascade="all, delete-orphan")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    description = Column(String, nullable=True)
    date = Column(String, nullable=False)

    owner = relationship("User", back_populates="expenses")