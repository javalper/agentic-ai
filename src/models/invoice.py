from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .subscriber import Base

class InvoiceStatus(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    PARTIAL = "partial"
    OVERDUE = "overdue"
    COLLECTION = "collection"
    WRITTEN_OFF = "written_off"

class Invoice(Base):
    __tablename__ = 'invoices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    subscriber_id = Column(Integer, ForeignKey('subscribers.id'), nullable=False, index=True)
    
    amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0.0)
    remaining_amount = Column(Float, nullable=False)
    
    issue_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    payment_date = Column(DateTime, nullable=True)
    
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.PENDING, nullable=False)
    
    billing_period_start = Column(DateTime)
    billing_period_end = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Invoice(id={self.id}, number={self.invoice_number}, amount={self.amount}, status={self.status})>"
    
    def days_overdue(self):
        if self.status == InvoiceStatus.PAID:
            return 0
        now = datetime.utcnow()
        if now > self.due_date:
            return (now - self.due_date).days
        return 0
    
    def update_status(self):
        if self.paid_amount >= self.amount:
            self.status = InvoiceStatus.PAID
            self.remaining_amount = 0.0
        elif self.paid_amount > 0:
            self.status = InvoiceStatus.PARTIAL
            self.remaining_amount = self.amount - self.paid_amount
        elif self.days_overdue() > 0:
            self.status = InvoiceStatus.OVERDUE
            self.remaining_amount = self.amount
        else:
            self.status = InvoiceStatus.PENDING
            self.remaining_amount = self.amount
