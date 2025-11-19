import sys
import argparse
from pathlib import Path
from datetime import datetime
import numpy as np
from sqlalchemy.orm import Session

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.database.db_manager import DatabaseManager
from src.models.subscriber import Subscriber
from src.models.invoice import Invoice
from src.models.collection_action import CollectionAction, CollectionChannel, ActionOutcome
from src.models.ml.logistic_regression import LogisticRegressionModel, FeatureExtractor
from src.config.settings import settings


def load_training_data(session: Session):
    actions = session.query(CollectionAction).filter(
        CollectionAction.outcome != ActionOutcome.PENDING
    ).all()
    
    if not actions:
        print("No training data available. Please run the system first to collect data.")
        return None, None
    
    print(f"Found {len(actions)} collection actions with outcomes")
    
    feature_extractor = FeatureExtractor()
    X_list = []
    y_list = []
    
    for action in actions:
        subscriber = session.query(Subscriber).filter(
            Subscriber.id == action.subscriber_id
        ).first()
        
        invoice = session.query(Invoice).filter(
            Invoice.id == action.invoice_id
        ).first()
        
        if subscriber and invoice:
            features = feature_extractor.extract_features(
                subscriber, invoice, action.channel
            )
            X_list.append(features)
            
            is_successful = 1 if action.is_successful() else 0
            y_list.append(is_successful)
    
    if not X_list:
        print("No valid training samples found.")
        return None, None
    
    X = np.array(X_list)
    y = np.array(y_list)
    
    print(f"Prepared {len(X)} training samples with {X.shape[1]} features")
    print(f"Success rate in training data: {np.mean(y):.2%}")
    
    return X, y


def train_model(
    session: Session,
    learning_rate: float = 0.01,
    max_iterations: int = 1000,
    regularization: float = 0.01,
    output_path: str = "models/logistic_regression.pkl"
):
    print("Loading training data...")
    X, y = load_training_data(session)
    
    if X is None or y is None:
        return None
    
    print("\nInitializing Logistic Regression model...")
    model = LogisticRegressionModel(
        learning_rate=learning_rate,
        max_iterations=max_iterations,
        regularization=regularization
    )
    
    print("\nTraining model...")
    print("=" * 50)
    model.fit(X, y, verbose=True)
    
    print("\n" + "=" * 50)
    print(model.summary())
    print("=" * 50)
    
    output_path = Path(output_path)
    model.save(str(output_path))
    print(f"\nModel saved to {output_path}")
    print(f"Metadata saved to {output_path.with_suffix('.json')}")
    
    return model


def evaluate_model(session: Session, model: LogisticRegressionModel):
    print("\nEvaluating model on training data...")
    X, y = load_training_data(session)
    
    if X is None or y is None:
        return
    
    predictions = model.predict(X)
    accuracy = np.mean(predictions == y)
    
    true_positives = np.sum((predictions == 1) & (y == 1))
    false_positives = np.sum((predictions == 1) & (y == 0))
    true_negatives = np.sum((predictions == 0) & (y == 0))
    false_negatives = np.sum((predictions == 0) & (y == 1))
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print("\nModel Evaluation Metrics:")
    print("=" * 50)
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1 Score: {f1_score:.4f}")
    print("\nConfusion Matrix:")
    print(f"  True Positives: {true_positives}")
    print(f"  False Positives: {false_positives}")
    print(f"  True Negatives: {true_negatives}")
    print(f"  False Negatives: {false_negatives}")
    print("=" * 50)


def test_predictions(session: Session, model: LogisticRegressionModel, n_samples: int = 5):
    print(f"\nTesting predictions on {n_samples} random samples...")
    print("=" * 50)
    
    subscribers = session.query(Subscriber).limit(n_samples).all()
    
    for subscriber in subscribers:
        invoices = session.query(Invoice).filter(
            Invoice.subscriber_id == subscriber.id
        ).limit(1).all()
        
        if not invoices:
            continue
        
        invoice = invoices[0]
        
        print(f"\nSubscriber: {subscriber.name} ({subscriber.subscriber_number})")
        print(f"  Age Group: {subscriber.age_group.value if subscriber.age_group else 'N/A'}")
        print(f"  Income Level: {subscriber.income_level.value if subscriber.income_level else 'N/A'}")
        print(f"  Payment Reliability: {subscriber.payment_reliability_score:.2f}")
        print(f"Invoice: {invoice.invoice_number}")
        print(f"  Amount: {invoice.amount:.2f}")
        print(f"  Days Overdue: {invoice.days_overdue()}")
        
        print("\nChannel Predictions:")
        channel_predictions = model.predict_all_channels(subscriber, invoice)
        
        for channel, (prediction, probability) in sorted(
            channel_predictions.items(),
            key=lambda x: x[1][1],
            reverse=True
        ):
            print(f"  {channel.value:30s}: {probability:.4f} ({'Success' if prediction == 1 else 'Failure'})")
        
        best_channel, confidence = model.get_best_channel(subscriber, invoice)
        print(f"\nRecommended Channel: {best_channel.value} (confidence: {confidence:.4f})")
        print("-" * 50)


def main():
    parser = argparse.ArgumentParser(description='Train Logistic Regression model for collection channel selection')
    parser.add_argument('--learning-rate', type=float, default=0.01, help='Learning rate for gradient descent')
    parser.add_argument('--max-iterations', type=int, default=1000, help='Maximum number of training iterations')
    parser.add_argument('--regularization', type=float, default=0.01, help='L2 regularization parameter')
    parser.add_argument('--output', type=str, default='models/logistic_regression.pkl', help='Output path for trained model')
    parser.add_argument('--evaluate', action='store_true', help='Evaluate model after training')
    parser.add_argument('--test', action='store_true', help='Test predictions on sample data')
    parser.add_argument('--test-samples', type=int, default=5, help='Number of samples to test')
    
    args = parser.parse_args()
    
    print("Initializing database connection...")
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    try:
        model = train_model(
            session,
            learning_rate=args.learning_rate,
            max_iterations=args.max_iterations,
            regularization=args.regularization,
            output_path=args.output
        )
        
        if model is None:
            print("\nTraining failed. Exiting.")
            return
        
        if args.evaluate:
            evaluate_model(session, model)
        
        if args.test:
            test_predictions(session, model, n_samples=args.test_samples)
        
        print("\nTraining completed successfully!")
        
    except Exception as e:
        print(f"\nError during training: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == '__main__':
    main()
