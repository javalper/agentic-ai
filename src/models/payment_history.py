from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from datetime import datetime
from .subscriber import Base

class PaymentHistory(Base):
    __tablename__ = 'payment_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False, index=True)
    subscriber_id = Column(Integer, ForeignKey('subscribers.id'), nullable=False, index=True)
    
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, nullable=False)
    payment_method = Column(String(50))
    
    days_after_due = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PaymentHistory(id={self.id}, invoice_id={self.invoice_id}, amount={self.amount})>"
