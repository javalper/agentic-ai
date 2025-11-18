from typing import List, Dict
from sqlalchemy.orm import Session
from datetime import datetime
import json

from ..models.subscriber import Subscriber
from ..models.invoice import Invoice, InvoiceStatus
from ..models.collection_action import CollectionAction, CollectionChannel, ActionOutcome
from .decision_engine import DecisionEngine
from .learning_engine import LearningEngine
from ..config.settings import settings

class CollectionAgent:
    def __init__(self, session: Session):
        self.session = session
        self.decision_engine = DecisionEngine(session)
        self.learning_engine = LearningEngine(session)
    
    def process_overdue_invoices(self) -> List[CollectionAction]:
        overdue_invoices = self.session.query(Invoice).filter(
            Invoice.status.in_([InvoiceStatus.OVERDUE, InvoiceStatus.PENDING])
        ).all()
        
        actions = []
        for invoice in overdue_invoices:
            if invoice.days_overdue() > 0:
                action = self.create_collection_action(invoice)
                if action:
                    actions.append(action)
        
        return actions
    
    def create_collection_action(self, invoice: Invoice) -> CollectionAction:
        subscriber = self.session.query(Subscriber).filter(
            Subscriber.id == invoice.subscriber_id
        ).first()
        
        if not subscriber:
            return None
        
        existing_action = self.session.query(CollectionAction).filter(
            CollectionAction.invoice_id == invoice.id,
            CollectionAction.outcome == ActionOutcome.PENDING
        ).first()
        
        if existing_action:
            return None
        
        channel, confidence, factors = self.decision_engine.select_collection_channel(
            subscriber, invoice
        )
        
        if confidence < settings.MIN_CONFIDENCE_THRESHOLD:
            channel = self._get_fallback_channel(invoice.days_overdue())
        
        action = CollectionAction(
            invoice_id=invoice.id,
            subscriber_id=subscriber.id,
            channel=channel,
            action_date=datetime.utcnow(),
            days_overdue_at_action=invoice.days_overdue(),
            amount_due=invoice.remaining_amount,
            outcome=ActionOutcome.PENDING,
            ai_confidence_score=confidence,
            decision_factors=json.dumps(factors)
        )
        
        self.session.add(action)
        self.session.commit()
        
        return action
    
    def _get_fallback_channel(self, days_overdue: int) -> CollectionChannel:
        if days_overdue <= settings.SMS_DAYS_THRESHOLD:
            return CollectionChannel.SMS
        elif days_overdue <= settings.IVR_DAYS_THRESHOLD:
            return CollectionChannel.IVR
        elif days_overdue <= settings.CALL_CENTER_DAYS_THRESHOLD:
            return CollectionChannel.CALL_CENTER
        else:
            return CollectionChannel.DEBT_COLLECTION_CENTER
    
    def update_action_outcome(
        self,
        action_id: int,
        outcome: ActionOutcome,
        amount_collected: float = 0.0
    ):
        action = self.session.query(CollectionAction).filter(
            CollectionAction.id == action_id
        ).first()
        
        if not action:
            return
        
        action.outcome = outcome
        action.outcome_date = datetime.utcnow()
        action.amount_collected = amount_collected
        
        self.session.commit()
        
        self.learning_engine.update_from_action_outcome(action)
        
        if outcome == ActionOutcome.SUCCESS:
            invoice = self.session.query(Invoice).filter(
                Invoice.id == action.invoice_id
            ).first()
            
            if invoice:
                invoice.paid_amount += amount_collected
                invoice.update_status()
        
        self.session.commit()
    
    def get_pending_actions(self) -> List[CollectionAction]:
        return self.session.query(CollectionAction).filter(
            CollectionAction.outcome == ActionOutcome.PENDING
        ).all()
    
    def get_actions_by_channel(self, channel: CollectionChannel) -> List[CollectionAction]:
        return self.session.query(CollectionAction).filter(
            CollectionAction.channel == channel,
            CollectionAction.outcome == ActionOutcome.PENDING
        ).all()
    
    def generate_action_report(self) -> Dict:
        pending_actions = self.get_pending_actions()
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_pending_actions': len(pending_actions),
            'actions_by_channel': {},
            'actions': []
        }
        
        for channel in CollectionChannel:
            channel_actions = [a for a in pending_actions if a.channel == channel]
            report['actions_by_channel'][channel.value] = len(channel_actions)
        
        for action in pending_actions:
            subscriber = self.session.query(Subscriber).filter(
                Subscriber.id == action.subscriber_id
            ).first()
            
            invoice = self.session.query(Invoice).filter(
                Invoice.id == action.invoice_id
            ).first()
            
            report['actions'].append({
                'action_id': action.id,
                'subscriber_number': subscriber.subscriber_number if subscriber else None,
                'subscriber_name': subscriber.name if subscriber else None,
                'invoice_number': invoice.invoice_number if invoice else None,
                'amount_due': action.amount_due,
                'channel': action.channel.value,
                'days_overdue': action.days_overdue_at_action,
                'confidence_score': action.ai_confidence_score,
                'action_date': action.action_date.isoformat()
            })
        
        return report
