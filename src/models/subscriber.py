from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class IncomeLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class AgeGroup(enum.Enum):
    YOUNG = "18-30"
    MIDDLE = "31-50"
    SENIOR = "51-70"
    ELDERLY = "70+"

class Subscriber(Base):
    __tablename__ = 'subscribers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    subscriber_number = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(20))
    email = Column(String(100))
    
    age_group = Column(Enum(AgeGroup), nullable=False)
    income_level = Column(Enum(IncomeLevel), nullable=False)
    region = Column(String(100))
    
    payment_reliability_score = Column(Float, default=0.5)
    average_days_late = Column(Float, default=0.0)
    total_invoices = Column(Integer, default=0)
    paid_on_time_count = Column(Integer, default=0)
    paid_late_count = Column(Integer, default=0)
    unpaid_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Subscriber(id={self.id}, number={self.subscriber_number}, name={self.name})>"
    
    def update_payment_score(self):
        if self.total_invoices > 0:
            on_time_ratio = self.paid_on_time_count / self.total_invoices
            late_ratio = self.paid_late_count / self.total_invoices
            unpaid_ratio = self.unpaid_count / self.total_invoices
            
            self.payment_reliability_score = (
                on_time_ratio * 1.0 + 
                late_ratio * 0.5 + 
                unpaid_ratio * 0.0
            )
