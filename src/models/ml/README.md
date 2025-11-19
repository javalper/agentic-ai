# Machine Learning Models

This module contains machine learning implementations for the Agentic AI debt collection system.

## Logistic Regression Model

The Logistic Regression model is used to predict the success probability of different collection channels for a given subscriber and invoice.

### Features

The model uses the following features for prediction:

1. **Subscriber Demographics**:
   - Age group (encoded: 0-3)
   - Income level (encoded: 0-2)
   - Payment reliability score (0.0-1.0)
   - Average days late

2. **Payment History**:
   - Paid on time ratio
   - Paid late ratio
   - Unpaid ratio

3. **Invoice Information**:
   - Days overdue
   - Log of days overdue
   - Invoice amount
   - Log of invoice amount
   - Remaining amount ratio

4. **Collection Channel**:
   - Channel type (encoded: 0-3)

### Training the Model

To train the logistic regression model, use the training script:

```bash
python -m src.scripts.train_logistic_regression
```

#### Training Options

```bash
python -m src.scripts.train_logistic_regression \
  --learning-rate 0.01 \
  --max-iterations 1000 \
  --regularization 0.01 \
  --output models/logistic_regression.pkl \
  --evaluate \
  --test \
  --test-samples 5
```

**Arguments**:
- `--learning-rate`: Learning rate for gradient descent (default: 0.01)
- `--max-iterations`: Maximum number of training iterations (default: 1000)
- `--regularization`: L2 regularization parameter (default: 0.01)
- `--output`: Output path for trained model (default: models/logistic_regression.pkl)
- `--evaluate`: Evaluate model after training
- `--test`: Test predictions on sample data
- `--test-samples`: Number of samples to test (default: 5)

### Using the Model

#### Basic Usage

```python
from src.models.ml.logistic_regression import LogisticRegressionModel
from src.models.subscriber import Subscriber
from src.models.invoice import Invoice
from src.models.collection_action import CollectionChannel

model = LogisticRegressionModel.load('models/logistic_regression.pkl')

prediction, probability = model.predict_single(subscriber, invoice, CollectionChannel.SMS)
print(f"Success probability: {probability:.2%}")

best_channel, confidence = model.get_best_channel(subscriber, invoice)
print(f"Best channel: {best_channel.value} (confidence: {confidence:.2%})")
```

#### Using with MLDecisionEngine

```python
from src.agent.ml_decision_engine import MLDecisionEngine
from src.database.db_manager import DatabaseManager

db_manager = DatabaseManager()
session = db_manager.get_session()

ml_engine = MLDecisionEngine(session, model_path='models/logistic_regression.pkl')

channel, confidence, factors = ml_engine.select_collection_channel(subscriber, invoice)
print(f"Selected channel: {channel.value}")
print(f"Confidence: {confidence:.2%}")

comparison = ml_engine.compare_methods(subscriber, invoice)
print(f"Rule-based: {comparison['rule_based']['channel']}")
print(f"ML-based: {comparison['ml_based']['channel']}")
print(f"Agreement: {comparison['agreement']}")
```

### Model Architecture

The implementation includes:

1. **LogisticRegressionModel**: Main model class with training and prediction methods
2. **FeatureExtractor**: Extracts and encodes features from subscriber and invoice data
3. **MLDecisionEngine**: Integrates ML model with existing rule-based decision engine

### Model Persistence

Models are saved in two files:
- `.pkl` file: Contains model weights and parameters (pickle format)
- `.json` file: Contains metadata and training history (human-readable)

### Feature Importance

After training, you can view feature importance:

```python
importance = model.get_feature_importance()
for feature, score in importance.items():
    print(f"{feature}: {score:.4f}")
```

### Model Summary

```python
print(model.summary())
```

Output includes:
- Training date and time
- Number of samples and features
- Final loss and accuracy
- Hyperparameters
- Top 5 most important features

## Implementation Details

### Gradient Descent

The model uses batch gradient descent with L2 regularization:

```
Loss = CrossEntropy + (λ/2m) * ||w||²
```

Where:
- CrossEntropy: Binary cross-entropy loss
- λ: Regularization parameter
- m: Number of samples
- w: Weight vector

### Convergence

Training stops when:
1. Maximum iterations reached, OR
2. Loss change < tolerance (default: 1e-6)

### Sigmoid Function

```
σ(z) = 1 / (1 + e^(-z))
```

With clipping to prevent overflow: z ∈ [-500, 500]

## Future Enhancements

Potential improvements:
1. Multi-class classification for predicting specific outcomes
2. Feature engineering (interaction terms, polynomial features)
3. Cross-validation for hyperparameter tuning
4. Online learning for continuous model updates
5. Ensemble methods (combining multiple models)
6. Deep learning models for complex patterns
