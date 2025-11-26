from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    provider = Column(String) # click, payme, uzum
    transaction_id = Column(String, unique=True, index=True) # ID from provider
    amount = Column(Float)
    currency = Column(String, default="UZS")
    status = Column(String) # created, paid, cancelled, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    perform_time = Column(DateTime(timezone=True), nullable=True)
    cancel_time = Column(DateTime(timezone=True), nullable=True)
    reason = Column(Integer, nullable=True) # For cancellation
    
    user = relationship("User", back_populates="transactions")
