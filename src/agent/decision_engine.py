from typing import Dict, List, Tuple
import numpy as np
from datetime import datetime
from sqlalchemy.orm import Session

from ..models.subscriber import Subscriber, AgeGroup, IncomeLevel
from ..models.invoice import Invoice
from ..models.collection_action import CollectionChannel
from ..models.channel_effectiveness import ChannelEffectiveness
from ..config.settings import settings

class DecisionEngine:
    def __init__(self, session: Session):
        self.session = session
        self.settings = settings
    
    def select_collection_channel(
        self, 
        subscriber: Subscriber, 
        invoice: Invoice
    ) -> Tuple[CollectionChannel, float, Dict]:
        days_overdue = invoice.days_overdue()
        
        channel_scores = {}
        decision_factors = {}
        
        for channel in CollectionChannel:
            score = self._calculate_channel_score(
                channel, subscriber, invoice, days_overdue
            )
            channel_scores[channel] = score
        
        best_channel = max(channel_scores, key=channel_scores.get)
        confidence = channel_scores[best_channel]
        
        decision_factors = {
            'days_overdue': days_overdue,
            'payment_reliability_score': subscriber.payment_reliability_score,
            'age_group': subscriber.age_group.value if subscriber.age_group else None,
            'income_level': subscriber.income_level.value if subscriber.income_level else None,
            'channel_scores': {ch.value: score for ch, score in channel_scores.items()}
        }
        
        return best_channel, confidence, decision_factors
    
    def _calculate_channel_score(
        self,
        channel: CollectionChannel,
        subscriber: Subscriber,
        invoice: Invoice,
        days_overdue: int
    ) -> float:
        score = 0.0
        
        days_score = self._calculate_days_overdue_score(channel, days_overdue)
        score += days_score * self.settings.CHANNEL_WEIGHTS['days_overdue']
        
        reliability_score = self._calculate_reliability_score(channel, subscriber)
        score += reliability_score * self.settings.CHANNEL_WEIGHTS['payment_reliability']
        
        historical_score = self._calculate_historical_success_score(channel, subscriber)
        score += historical_score * self.settings.CHANNEL_WEIGHTS['historical_success']
        
        demographic_score = self._calculate_demographic_score(channel, subscriber)
        score += demographic_score * self.settings.CHANNEL_WEIGHTS['demographic']
        
        return score
    
    def _calculate_days_overdue_score(
        self, 
        channel: CollectionChannel, 
        days_overdue: int
    ) -> float:
        if channel == CollectionChannel.SMS:
            if days_overdue <= self.settings.SMS_DAYS_THRESHOLD:
                return 1.0
            elif days_overdue <= self.settings.IVR_DAYS_THRESHOLD:
                return 0.6
            else:
                return 0.2
        
        elif channel == CollectionChannel.IVR:
            if days_overdue <= self.settings.SMS_DAYS_THRESHOLD:
                return 0.5
            elif days_overdue <= self.settings.IVR_DAYS_THRESHOLD:
                return 1.0
            elif days_overdue <= self.settings.CALL_CENTER_DAYS_THRESHOLD:
                return 0.7
            else:
                return 0.3
        
        elif channel == CollectionChannel.CALL_CENTER:
            if days_overdue <= self.settings.IVR_DAYS_THRESHOLD:
                return 0.3
            elif days_overdue <= self.settings.CALL_CENTER_DAYS_THRESHOLD:
                return 1.0
            else:
                return 0.8
        
        elif channel == CollectionChannel.DEBT_COLLECTION_CENTER:
            if days_overdue <= self.settings.CALL_CENTER_DAYS_THRESHOLD:
                return 0.1
            else:
                return 1.0
        
        return 0.5
    
    def _calculate_reliability_score(
        self,
        channel: CollectionChannel,
        subscriber: Subscriber
    ) -> float:
        reliability = subscriber.payment_reliability_score
        
        if channel == CollectionChannel.SMS:
            if reliability > 0.7:
                return 1.0
            elif reliability > 0.4:
                return 0.7
            else:
                return 0.3
        
        elif channel == CollectionChannel.IVR:
            if reliability > 0.5:
                return 0.9
            elif reliability > 0.3:
                return 1.0
            else:
                return 0.5
        
        elif channel == CollectionChannel.CALL_CENTER:
            if reliability > 0.5:
                return 0.6
            elif reliability > 0.3:
                return 0.9
            else:
                return 1.0
        
        elif channel == CollectionChannel.DEBT_COLLECTION_CENTER:
            if reliability < 0.3:
                return 1.0
            else:
                return 0.2
        
        return 0.5
    
    def _calculate_historical_success_score(
        self,
        channel: CollectionChannel,
        subscriber: Subscriber
    ) -> float:
        effectiveness = self.session.query(ChannelEffectiveness).filter(
            ChannelEffectiveness.subscriber_id == subscriber.id,
            ChannelEffectiveness.channel == channel
        ).first()
        
        if effectiveness and effectiveness.total_attempts > 0:
            return effectiveness.success_rate
        
        general_effectiveness = self.session.query(ChannelEffectiveness).filter(
            ChannelEffectiveness.subscriber_id.is_(None),
            ChannelEffectiveness.channel == channel,
            ChannelEffectiveness.age_group == subscriber.age_group,
            ChannelEffectiveness.income_level == subscriber.income_level
        ).first()
        
        if general_effectiveness and general_effectiveness.total_attempts > 0:
            return general_effectiveness.success_rate * 0.8
        
        return 0.5
    
    def _calculate_demographic_score(
        self,
        channel: CollectionChannel,
        subscriber: Subscriber
    ) -> float:
        score = 0.5
        
        if subscriber.age_group:
            age_group_key = subscriber.age_group.name
            preferred_channels = self.settings.DEMOGRAPHIC_PREFERENCES.get(age_group_key, [])
            
            if channel.value in preferred_channels:
                position = preferred_channels.index(channel.value)
                score = 1.0 - (position * 0.2)
        
        if subscriber.income_level:
            income_threshold = self.settings.INCOME_LEVEL_THRESHOLDS.get(
                subscriber.income_level.name, 0.5
            )
            
            if channel == CollectionChannel.CALL_CENTER:
                score = (score + (1.0 - income_threshold)) / 2
            elif channel == CollectionChannel.SMS:
                score = (score + income_threshold) / 2
        
        return max(0.0, min(1.0, score))
