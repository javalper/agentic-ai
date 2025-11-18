from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from datetime import datetime
from .collection_action import CollectionChannel
from .subscriber import Base, AgeGroup, IncomeLevel

class ChannelEffectiveness(Base):
    __tablename__ = 'channel_effectiveness'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    subscriber_id = Column(Integer, ForeignKey('subscribers.id'), nullable=True, index=True)
    
    channel = Column(Enum(CollectionChannel), nullable=False)
    
    age_group = Column(Enum(AgeGroup), nullable=True)
    income_level = Column(Enum(IncomeLevel), nullable=True)
    region = Column(String(100), nullable=True)
    
    total_attempts = Column(Integer, default=0)
    successful_attempts = Column(Integer, default=0)
    failed_attempts = Column(Integer, default=0)
    
    success_rate = Column(Float, default=0.0)
    average_collection_rate = Column(Float, default=0.0)
    average_response_time = Column(Float, default=0.0)
    
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ChannelEffectiveness(channel={self.channel}, success_rate={self.success_rate})>"
    
    def update_metrics(self):
        if self.total_attempts > 0:
            self.success_rate = self.successful_attempts / self.total_attempts
        else:
            self.success_rate = 0.0
