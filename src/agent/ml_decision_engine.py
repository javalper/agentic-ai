from typing import Dict, List, Tuple, Optional
import numpy as np
from datetime import datetime
from sqlalchemy.orm import Session

from ..models.subscriber import Subscriber, AgeGroup, IncomeLevel
from ..models.invoice import Invoice
from ..models.collection_action import CollectionChannel
from ..models.channel_effectiveness import ChannelEffectiveness
from ..models.ml.logistic_regression import LogisticRegressionModel
from ..config.settings import settings
from .decision_engine import DecisionEngine


class MLDecisionEngine(DecisionEngine):
    def __init__(self, session: Session, model_path: Optional[str] = None):
        super().__init__(session)
        self.ml_model: Optional[LogisticRegressionModel] = None
        self.use_ml = False
        
        if model_path:
            try:
                self.ml_model = LogisticRegressionModel.load(model_path)
                self.use_ml = True
                print(f"ML model loaded from {model_path}")
            except Exception as e:
                print(f"Failed to load ML model: {e}")
                print("Falling back to rule-based decision engine")
    
    def select_collection_channel(
        self, 
        subscriber: Subscriber, 
        invoice: Invoice,
        use_ml: Optional[bool] = None
    ) -> Tuple[CollectionChannel, float, Dict]:
        if use_ml is None:
            use_ml = self.use_ml
        
        if use_ml and self.ml_model is not None:
            return self._select_channel_ml(subscriber, invoice)
        else:
            return super().select_collection_channel(subscriber, invoice)
    
    def _select_channel_ml(
        self,
        subscriber: Subscriber,
        invoice: Invoice
    ) -> Tuple[CollectionChannel, float, Dict]:
        best_channel, confidence = self.ml_model.get_best_channel(subscriber, invoice)
        
        channel_predictions = self.ml_model.predict_all_channels(subscriber, invoice)
        
        decision_factors = {
            'days_overdue': invoice.days_overdue(),
            'payment_reliability_score': subscriber.payment_reliability_score,
            'age_group': subscriber.age_group.value if subscriber.age_group else None,
            'income_level': subscriber.income_level.value if subscriber.income_level else None,
            'ml_predictions': {
                ch.value: {'prediction': pred, 'probability': prob}
                for ch, (pred, prob) in channel_predictions.items()
            },
            'selected_channel': best_channel.value,
            'confidence': confidence,
            'method': 'ml'
        }
        
        return best_channel, confidence, decision_factors
    
    def compare_methods(
        self,
        subscriber: Subscriber,
        invoice: Invoice
    ) -> Dict:
        rule_based_channel, rule_confidence, rule_factors = super().select_collection_channel(
            subscriber, invoice
        )
        
        comparison = {
            'rule_based': {
                'channel': rule_based_channel.value,
                'confidence': rule_confidence,
                'factors': rule_factors
            }
        }
        
        if self.ml_model is not None:
            ml_channel, ml_confidence, ml_factors = self._select_channel_ml(
                subscriber, invoice
            )
            comparison['ml_based'] = {
                'channel': ml_channel.value,
                'confidence': ml_confidence,
                'factors': ml_factors
            }
            comparison['agreement'] = (rule_based_channel == ml_channel)
        
        return comparison
    
    def get_model_summary(self) -> str:
        if self.ml_model is None:
            return "No ML model loaded"
        return self.ml_model.summary()
