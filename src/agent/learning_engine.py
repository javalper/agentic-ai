from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from ..models.collection_action import CollectionAction, CollectionChannel, ActionOutcome
from ..models.channel_effectiveness import ChannelEffectiveness
from ..models.subscriber import Subscriber, AgeGroup, IncomeLevel
from ..config.settings import settings

class LearningEngine:
    def __init__(self, session: Session):
        self.session = session
        self.learning_rate = settings.LEARNING_RATE
    
    def update_from_action_outcome(self, action: CollectionAction):
        if action.outcome == ActionOutcome.PENDING:
            return
        
        self._update_subscriber_specific_effectiveness(action)
        self._update_demographic_effectiveness(action)
        self._update_subscriber_payment_profile(action)
    
    def _update_subscriber_specific_effectiveness(self, action: CollectionAction):
        effectiveness = self.session.query(ChannelEffectiveness).filter(
            ChannelEffectiveness.subscriber_id == action.subscriber_id,
            ChannelEffectiveness.channel == action.channel
        ).first()
        
        if not effectiveness:
            effectiveness = ChannelEffectiveness(
                subscriber_id=action.subscriber_id,
                channel=action.channel,
                total_attempts=0,
                successful_attempts=0,
                failed_attempts=0
            )
            self.session.add(effectiveness)
        
        effectiveness.total_attempts += 1
        
        if action.is_successful():
            effectiveness.successful_attempts += 1
        else:
            effectiveness.failed_attempts += 1
        
        effectiveness.update_metrics()
        
        if action.amount_collected > 0:
            collection_rate = action.amount_collected / action.amount_due
            if effectiveness.average_collection_rate is None or effectiveness.average_collection_rate == 0:
                effectiveness.average_collection_rate = collection_rate
            else:
                effectiveness.average_collection_rate = (
                    effectiveness.average_collection_rate * (1 - self.learning_rate) +
                    collection_rate * self.learning_rate
                )
    
    def _update_demographic_effectiveness(self, action: CollectionAction):
        subscriber = self.session.query(Subscriber).filter(
            Subscriber.id == action.subscriber_id
        ).first()
        
        if not subscriber:
            return
        
        effectiveness = self.session.query(ChannelEffectiveness).filter(
            ChannelEffectiveness.subscriber_id.is_(None),
            ChannelEffectiveness.channel == action.channel,
            ChannelEffectiveness.age_group == subscriber.age_group,
            ChannelEffectiveness.income_level == subscriber.income_level,
            ChannelEffectiveness.region == subscriber.region
        ).first()
        
        if not effectiveness:
            effectiveness = ChannelEffectiveness(
                subscriber_id=None,
                channel=action.channel,
                age_group=subscriber.age_group,
                income_level=subscriber.income_level,
                region=subscriber.region,
                total_attempts=0,
                successful_attempts=0,
                failed_attempts=0
            )
            self.session.add(effectiveness)
        
        effectiveness.total_attempts += 1
        
        if action.is_successful():
            effectiveness.successful_attempts += 1
        else:
            effectiveness.failed_attempts += 1
        
        effectiveness.update_metrics()
    
    def _update_subscriber_payment_profile(self, action: CollectionAction):
        subscriber = self.session.query(Subscriber).filter(
            Subscriber.id == action.subscriber_id
        ).first()
        
        if not subscriber:
            return
        
        if action.outcome == ActionOutcome.SUCCESS:
            if action.days_overdue_at_action == 0:
                subscriber.paid_on_time_count += 1
            else:
                subscriber.paid_late_count += 1
            
            if subscriber.average_days_late == 0:
                subscriber.average_days_late = action.days_overdue_at_action
            else:
                subscriber.average_days_late = (
                    subscriber.average_days_late * (1 - self.learning_rate) +
                    action.days_overdue_at_action * self.learning_rate
                )
        
        elif action.outcome in [ActionOutcome.FAILED, ActionOutcome.NO_RESPONSE]:
            subscriber.unpaid_count += 1
        
        subscriber.update_payment_score()
    
    def get_channel_recommendations(
        self, 
        subscriber: Subscriber
    ) -> List[tuple]:
        effectiveness_records = self.session.query(ChannelEffectiveness).filter(
            ChannelEffectiveness.subscriber_id == subscriber.id
        ).all()
        
        if not effectiveness_records:
            effectiveness_records = self.session.query(ChannelEffectiveness).filter(
                ChannelEffectiveness.subscriber_id.is_(None),
                ChannelEffectiveness.age_group == subscriber.age_group,
                ChannelEffectiveness.income_level == subscriber.income_level
            ).all()
        
        recommendations = []
        for record in effectiveness_records:
            if record.total_attempts >= 3:
                recommendations.append((
                    record.channel,
                    record.success_rate,
                    record.average_collection_rate
                ))
        
        recommendations.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        return recommendations
    
    def analyze_system_performance(self) -> dict:
        total_actions = self.session.query(func.count(CollectionAction.id)).scalar()
        
        successful_actions = self.session.query(func.count(CollectionAction.id)).filter(
            CollectionAction.outcome.in_([ActionOutcome.SUCCESS, ActionOutcome.PARTIAL_SUCCESS])
        ).scalar()
        
        overall_success_rate = successful_actions / total_actions if total_actions > 0 else 0
        
        channel_performance = {}
        for channel in CollectionChannel:
            channel_total = self.session.query(func.count(CollectionAction.id)).filter(
                CollectionAction.channel == channel
            ).scalar()
            
            channel_success = self.session.query(func.count(CollectionAction.id)).filter(
                CollectionAction.channel == channel,
                CollectionAction.outcome.in_([ActionOutcome.SUCCESS, ActionOutcome.PARTIAL_SUCCESS])
            ).scalar()
            
            channel_performance[channel.value] = {
                'total_attempts': channel_total,
                'successful_attempts': channel_success,
                'success_rate': channel_success / channel_total if channel_total > 0 else 0
            }
        
        return {
            'total_actions': total_actions,
            'successful_actions': successful_actions,
            'overall_success_rate': overall_success_rate,
            'channel_performance': channel_performance
        }
