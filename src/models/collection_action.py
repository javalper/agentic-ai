from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Float, Boolean
from datetime import datetime
import enum
from .subscriber import Base

class CollectionChannel(enum.Enum):
    SMS = "sms"
    IVR = "ivr"
    CALL_CENTER = "call_center"
    DEBT_COLLECTION_CENTER = "debt_collection_center"

class ActionOutcome(enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    NO_RESPONSE = "no_response"

class CollectionAction(Base):
    __tablename__ = 'collection_actions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False, index=True)
    subscriber_id = Column(Integer, ForeignKey('subscribers.id'), nullable=False, index=True)
    
    channel = Column(Enum(CollectionChannel), nullable=False)
    action_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    days_overdue_at_action = Column(Integer, nullable=False)
    amount_due = Column(Float, nullable=False)
    
    outcome = Column(Enum(ActionOutcome), default=ActionOutcome.PENDING)
    outcome_date = Column(DateTime, nullable=True)
    amount_collected = Column(Float, default=0.0)
    
    ai_confidence_score = Column(Float)
    decision_factors = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<CollectionAction(id={self.id}, channel={self.channel}, outcome={self.outcome})>"
    
    def is_successful(self):
        return self.outcome in [ActionOutcome.SUCCESS, ActionOutcome.PARTIAL_SUCCESS]
