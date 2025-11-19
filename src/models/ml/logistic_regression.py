import numpy as np
import pickle
import json
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from datetime import datetime

from ..subscriber import Subscriber, AgeGroup, IncomeLevel
from ..invoice import Invoice
from ..collection_action import CollectionChannel, ActionOutcome


class FeatureExtractor:
    def __init__(self):
        self.age_group_mapping = {
            AgeGroup.YOUNG: 0,
            AgeGroup.MIDDLE: 1,
            AgeGroup.SENIOR: 2,
            AgeGroup.ELDERLY: 3
        }
        
        self.income_level_mapping = {
            IncomeLevel.LOW: 0,
            IncomeLevel.MEDIUM: 1,
            IncomeLevel.HIGH: 2
        }
        
        self.channel_mapping = {
            CollectionChannel.SMS: 0,
            CollectionChannel.IVR: 1,
            CollectionChannel.CALL_CENTER: 2,
            CollectionChannel.DEBT_COLLECTION_CENTER: 3
        }
    
    def extract_features(
        self, 
        subscriber: Subscriber, 
        invoice: Invoice,
        channel: CollectionChannel
    ) -> np.ndarray:
        features = []
        
        features.append(self.age_group_mapping.get(subscriber.age_group, 0))
        features.append(self.income_level_mapping.get(subscriber.income_level, 0))
        features.append(subscriber.payment_reliability_score)
        features.append(subscriber.average_days_late)
        
        total_invoices = subscriber.total_invoices if subscriber.total_invoices > 0 else 1
        features.append(subscriber.paid_on_time_count / total_invoices)
        features.append(subscriber.paid_late_count / total_invoices)
        features.append(subscriber.unpaid_count / total_invoices)
        
        days_overdue = invoice.days_overdue()
        features.append(days_overdue)
        features.append(np.log1p(days_overdue))
        
        features.append(invoice.amount)
        features.append(np.log1p(invoice.amount))
        features.append(invoice.remaining_amount / invoice.amount if invoice.amount > 0 else 1.0)
        
        features.append(self.channel_mapping.get(channel, 0))
        
        return np.array(features, dtype=np.float64)
    
    def get_feature_names(self) -> List[str]:
        return [
            'age_group',
            'income_level',
            'payment_reliability_score',
            'average_days_late',
            'paid_on_time_ratio',
            'paid_late_ratio',
            'unpaid_ratio',
            'days_overdue',
            'log_days_overdue',
            'invoice_amount',
            'log_invoice_amount',
            'remaining_amount_ratio',
            'channel'
        ]


class LogisticRegressionModel:
    def __init__(self, learning_rate: float = 0.01, max_iterations: int = 1000, 
                 regularization: float = 0.01, tolerance: float = 1e-6):
        self.learning_rate = learning_rate
        self.max_iterations = max_iterations
        self.regularization = regularization
        self.tolerance = tolerance
        
        self.weights: Optional[np.ndarray] = None
        self.bias: float = 0.0
        self.feature_extractor = FeatureExtractor()
        
        self.training_history: Dict = {
            'loss': [],
            'accuracy': [],
            'iterations': 0
        }
        
        self.metadata: Dict = {
            'trained_at': None,
            'n_samples': 0,
            'n_features': 0,
            'final_loss': None,
            'final_accuracy': None
        }
    
    def _sigmoid(self, z: np.ndarray) -> np.ndarray:
        return 1 / (1 + np.exp(-np.clip(z, -500, 500)))
    
    def _compute_loss(self, X: np.ndarray, y: np.ndarray) -> float:
        m = X.shape[0]
        predictions = self._sigmoid(np.dot(X, self.weights) + self.bias)
        
        epsilon = 1e-15
        predictions = np.clip(predictions, epsilon, 1 - epsilon)
        
        cross_entropy_loss = -np.mean(
            y * np.log(predictions) + (1 - y) * np.log(1 - predictions)
        )
        
        l2_penalty = (self.regularization / (2 * m)) * np.sum(self.weights ** 2)
        
        return cross_entropy_loss + l2_penalty
    
    def _compute_accuracy(self, X: np.ndarray, y: np.ndarray) -> float:
        predictions = self.predict(X)
        return np.mean(predictions == y)
    
    def fit(self, X: np.ndarray, y: np.ndarray, verbose: bool = True) -> 'LogisticRegressionModel':
        m, n = X.shape
        
        self.weights = np.zeros(n)
        self.bias = 0.0
        
        self.training_history = {
            'loss': [],
            'accuracy': [],
            'iterations': 0
        }
        
        for iteration in range(self.max_iterations):
            predictions = self._sigmoid(np.dot(X, self.weights) + self.bias)
            
            dw = (1 / m) * np.dot(X.T, (predictions - y)) + (self.regularization / m) * self.weights
            db = (1 / m) * np.sum(predictions - y)
            
            self.weights -= self.learning_rate * dw
            self.bias -= self.learning_rate * db
            
            if iteration % 100 == 0:
                loss = self._compute_loss(X, y)
                accuracy = self._compute_accuracy(X, y)
                
                self.training_history['loss'].append(loss)
                self.training_history['accuracy'].append(accuracy)
                
                if verbose:
                    print(f"Iteration {iteration}: Loss = {loss:.4f}, Accuracy = {accuracy:.4f}")
                
                if len(self.training_history['loss']) > 1:
                    loss_diff = abs(self.training_history['loss'][-1] - self.training_history['loss'][-2])
                    if loss_diff < self.tolerance:
                        if verbose:
                            print(f"Converged at iteration {iteration}")
                        break
        
        self.training_history['iterations'] = iteration + 1
        
        final_loss = self._compute_loss(X, y)
        final_accuracy = self._compute_accuracy(X, y)
        
        self.metadata = {
            'trained_at': datetime.utcnow().isoformat(),
            'n_samples': m,
            'n_features': n,
            'final_loss': float(final_loss),
            'final_accuracy': float(final_accuracy)
        }
        
        if verbose:
            print(f"\nTraining completed:")
            print(f"  Samples: {m}")
            print(f"  Features: {n}")
            print(f"  Final Loss: {final_loss:.4f}")
            print(f"  Final Accuracy: {final_accuracy:.4f}")
        
        return self
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.weights is None:
            raise ValueError("Model has not been trained yet. Call fit() first.")
        
        return self._sigmoid(np.dot(X, self.weights) + self.bias)
    
    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        probabilities = self.predict_proba(X)
        return (probabilities >= threshold).astype(int)
    
    def predict_single(
        self, 
        subscriber: Subscriber, 
        invoice: Invoice,
        channel: CollectionChannel,
        threshold: float = 0.5
    ) -> Tuple[int, float]:
        features = self.feature_extractor.extract_features(subscriber, invoice, channel)
        features = features.reshape(1, -1)
        
        probability = self.predict_proba(features)[0]
        prediction = int(probability >= threshold)
        
        return prediction, float(probability)
    
    def predict_all_channels(
        self,
        subscriber: Subscriber,
        invoice: Invoice
    ) -> Dict[CollectionChannel, Tuple[int, float]]:
        results = {}
        
        for channel in CollectionChannel:
            prediction, probability = self.predict_single(subscriber, invoice, channel)
            results[channel] = (prediction, probability)
        
        return results
    
    def get_best_channel(
        self,
        subscriber: Subscriber,
        invoice: Invoice
    ) -> Tuple[CollectionChannel, float]:
        channel_predictions = self.predict_all_channels(subscriber, invoice)
        
        best_channel = max(
            channel_predictions.items(),
            key=lambda x: x[1][1]
        )
        
        return best_channel[0], best_channel[1][1]
    
    def save(self, filepath: str):
        model_data = {
            'weights': self.weights.tolist() if self.weights is not None else None,
            'bias': self.bias,
            'learning_rate': self.learning_rate,
            'max_iterations': self.max_iterations,
            'regularization': self.regularization,
            'tolerance': self.tolerance,
            'training_history': self.training_history,
            'metadata': self.metadata
        }
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        metadata_path = filepath.with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump({
                'metadata': self.metadata,
                'training_history': self.training_history,
                'feature_names': self.feature_extractor.get_feature_names()
            }, f, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> 'LogisticRegressionModel':
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        model = cls(
            learning_rate=model_data['learning_rate'],
            max_iterations=model_data['max_iterations'],
            regularization=model_data['regularization'],
            tolerance=model_data['tolerance']
        )
        
        model.weights = np.array(model_data['weights']) if model_data['weights'] is not None else None
        model.bias = model_data['bias']
        model.training_history = model_data['training_history']
        model.metadata = model_data['metadata']
        
        return model
    
    def get_feature_importance(self) -> Dict[str, float]:
        if self.weights is None:
            raise ValueError("Model has not been trained yet. Call fit() first.")
        
        feature_names = self.feature_extractor.get_feature_names()
        importance = dict(zip(feature_names, np.abs(self.weights)))
        
        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
    
    def summary(self) -> str:
        if self.weights is None:
            return "Model has not been trained yet."
        
        summary_lines = [
            "Logistic Regression Model Summary",
            "=" * 50,
            f"Trained at: {self.metadata.get('trained_at', 'N/A')}",
            f"Training samples: {self.metadata.get('n_samples', 0)}",
            f"Number of features: {self.metadata.get('n_features', 0)}",
            f"Final loss: {self.metadata.get('final_loss', 0):.4f}",
            f"Final accuracy: {self.metadata.get('final_accuracy', 0):.4f}",
            f"Iterations: {self.training_history.get('iterations', 0)}",
            "",
            "Hyperparameters:",
            f"  Learning rate: {self.learning_rate}",
            f"  Regularization: {self.regularization}",
            f"  Max iterations: {self.max_iterations}",
            "",
            "Top 5 Feature Importance:",
        ]
        
        feature_importance = self.get_feature_importance()
        for i, (feature, importance) in enumerate(list(feature_importance.items())[:5], 1):
            summary_lines.append(f"  {i}. {feature}: {importance:.4f}")
        
        return "\n".join(summary_lines)
