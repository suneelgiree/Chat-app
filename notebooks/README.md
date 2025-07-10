## Trained Sentiment Model

### Model Details
- **File**: `sentiment_model.pkl`
- **Dataset**: IMDb Dataset of 50K Movie Reviews
- **Algorithm**: Random Forest Classifier
- **Preprocessing**: TF-IDF with 5000 features

### Performance
- **Accuracy**: 85.2%
- **Precision**: 84.8%
- **Recall**: 85.5%

### Usage
To use the model, load it as follows:
```python
import joblib

model = joblib.load('sentiment_model.pkl')