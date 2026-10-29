import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, roc_auc_score
from sklearn.pipeline import Pipeline
import joblib
import re
import os

# Basic stopwords list (no NLTK dependency)
BASIC_STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
    'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
    'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
    'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
    'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
    'while', 'of', 'at', 'by', 'for', 'with', 'through', 'during', 'before', 'after',
    'above', 'below', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
    'further', 'then', 'once'
}

class FakeJobDetector:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8,
            sublinear_tf=True  # Apply sublinear tf scaling
        )
        self.model = LogisticRegression(
            random_state=42, 
            max_iter=1000,
            C=1.0,  # Regularization parameter
            solver='liblinear'  # Good for small datasets
        )
        self.stop_words = BASIC_STOPWORDS
        self.best_model = None
        self.best_vectorizer = None
    
    def preprocess_text(self, text):
        """Clean and preprocess text data"""
        if pd.isna(text):
            return ""
        
        # Convert to lowercase
        text = str(text).lower()
        
        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def combine_features(self, row):
        """Combine all text features into one string"""
        features = []
        # Map to actual column names in the dataset
        # For the fake_job_postings.csv dataset
        text_columns = ['title', 'location', 'department', 'company_profile', 'description', 
                       'requirements', 'benefits', 'employment_type', 'required_experience', 
                       'required_education', 'industry', 'function']
        
        for col in text_columns:
            if col in row.index and pd.notna(row[col]):
                features.append(str(row[col]))
        return ' '.join(features)
    
    def hyperparameter_tuning(self, X_train, y_train):
        """Perform hyperparameter tuning for better model performance"""
        print("Performing hyperparameter tuning...")
        
        # Define parameter grid for Logistic Regression
        param_grid = {
            'C': [0.1, 1, 10, 100],
            'solver': ['liblinear', 'lbfgs'],
            'max_iter': [1000, 2000]
        }
        
        # Create pipeline
        pipeline = Pipeline([
            ('tfidf', self.vectorizer),
            ('classifier', self.model)
        ])
        
        # Perform grid search
        grid_search = GridSearchCV(
            pipeline, 
            param_grid, 
            cv=5, 
            scoring='accuracy',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train, y_train)
        
        print(f"Best parameters: {grid_search.best_params_}")
        print(f"Best cross-validation score: {grid_search.best_score_:.4f}")
        
        return grid_search.best_estimator_
    
    def train_advanced_models(self, X_train, X_test, y_train, y_test):
        """Train multiple models and compare performance"""
        print("Training multiple models for comparison...")
        
        # Models to compare
        models = {
            'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
            'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'Naive Bayes': MultinomialNB()
        }
        
        results = {}
        
        for name, model in models.items():
            print(f"\nTraining {name}...")
            
            # Create pipeline
            pipeline = Pipeline([
                ('tfidf', TfidfVectorizer(
                    max_features=5000,
                    stop_words='english',
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.8
                )),
                ('classifier', model)
            ])
            
            # Train model
            pipeline.fit(X_train, y_train)
            
            # Predictions
            y_pred = pipeline.predict(X_test)
            y_prob = pipeline.predict_proba(X_test)[:, 1]
            
            # Evaluation metrics
            accuracy = accuracy_score(y_test, y_pred)
            auc_score = roc_auc_score(y_test, y_prob)
            
            results[name] = {
                'model': pipeline,
                'accuracy': accuracy,
                'auc': auc_score
            }
            
            print(f"{name} - Accuracy: {accuracy:.4f}, AUC: {auc_score:.4f}")
        
        # Select best model based on accuracy
        best_model_name = max(results.keys(), key=lambda x: results[x]['accuracy'])
        self.best_model = results[best_model_name]['model']
        
        print(f"\nBest model: {best_model_name}")
        return results
    
    def load_multiple_datasets(self, data_paths):
        """Load and combine multiple datasets"""
        dataframes = []
        
        for path in data_paths:
            if os.path.exists(path):
                print(f"Loading dataset: {path}")
                df = pd.read_csv(path)
                print(f"  - Loaded {len(df)} records")
                dataframes.append(df)
            else:
                print(f"  - Warning: {path} not found, skipping")
        
        if not dataframes:
            raise FileNotFoundError("No valid datasets found")
        
        # Combine all datasets
        combined_df = pd.concat(dataframes, ignore_index=True)
        print(f"Combined dataset shape: {combined_df.shape}")
        
        return combined_df
    
    def train(self, data_paths, advanced_training=True):
        """Train the fake job detection model with multiple datasets"""
        print("Loading datasets...")
        df = self.load_multiple_datasets(data_paths)
        
        print(f"Total dataset shape: {df.shape}")
        print(f"Fraudulent jobs: {df['fraudulent'].sum()}")
        print(f"Legitimate jobs: {len(df) - df['fraudulent'].sum()}")
        
        # Check for class imbalance
        fraud_ratio = df['fraudulent'].sum() / len(df)
        print(f"Fraud ratio: {fraud_ratio:.4f}")
        
        # Combine all text features
        print("Preprocessing text data...")
        df['combined_text'] = df.apply(self.combine_features, axis=1)
        df['processed_text'] = df['combined_text'].apply(self.preprocess_text)
        
        # Prepare features and target
        X = df['processed_text']
        y = df['fraudulent']
        
        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"Training set size: {len(X_train)}")
        print(f"Test set size: {len(X_test)}")
        
        if advanced_training:
            # Train multiple models and compare
            model_results = self.train_advanced_models(X_train, X_test, y_train, y_test)
            
            # Use the best model
            best_model_name = max(model_results.keys(), key=lambda x: model_results[x]['accuracy'])
            best_pipeline = model_results[best_model_name]['model']
            
            # Extract vectorizer and model from pipeline
            self.vectorizer = best_pipeline.named_steps['tfidf']
            self.model = best_pipeline.named_steps['classifier']
            
            # Final evaluation
            y_pred = best_pipeline.predict(X_test)
            y_prob = best_pipeline.predict_proba(X_test)[:, 1]
            
            accuracy = accuracy_score(y_test, y_pred)
            auc_score = roc_auc_score(y_test, y_prob)
            
            print(f"\nFinal Model Performance ({best_model_name}):")
            print(f"Accuracy: {accuracy:.4f}")
            print(f"AUC Score: {auc_score:.4f}")
            print("\nClassification Report:")
            print(classification_report(y_test, y_pred))
            print("\nConfusion Matrix:")
            print(confusion_matrix(y_test, y_pred))
            
        else:
            print("Vectorizing text data...")
            # Fit and transform the training data
            X_train_tfidf = self.vectorizer.fit_transform(X_train)
            X_test_tfidf = self.vectorizer.transform(X_test)
            
            print("Training model...")
            # Train the model
            self.model.fit(X_train_tfidf, y_train)
            
            # Make predictions
            y_pred = self.model.predict(X_test_tfidf)
            y_prob = self.model.predict_proba(X_test_tfidf)[:, 1]
            
            # Evaluate the model
            accuracy = accuracy_score(y_test, y_pred)
            auc_score = roc_auc_score(y_test, y_prob)
            
            print(f"\nModel Accuracy: {accuracy:.4f}")
            print(f"AUC Score: {auc_score:.4f}")
            print("\nClassification Report:")
            print(classification_report(y_test, y_pred))
            print("\nConfusion Matrix:")
            print(confusion_matrix(y_test, y_pred))
        
        # Cross-validation
        print("\nPerforming cross-validation...")
        pipeline = Pipeline([
            ('tfidf', self.vectorizer),
            ('classifier', self.model)
        ])
        
        cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='accuracy')
        print(f"Cross-validation scores: {cv_scores}")
        print(f"Mean CV accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
        
        # Save the model and vectorizer
        print("Saving model and vectorizer...")
        os.makedirs('models', exist_ok=True)
        joblib.dump(self.model, 'models/fake_job_model.pkl')
        joblib.dump(self.vectorizer, 'models/tfidf_vectorizer.pkl')
        
        print("Model training completed successfully!")
        return accuracy
    
    def predict(self, text):
        """Predict if a job posting is fake or real"""
        processed_text = self.preprocess_text(text)
        text_tfidf = self.vectorizer.transform([processed_text])
        prediction = self.model.predict(text_tfidf)[0]
        probability = self.model.predict_proba(text_tfidf)[0]
        
        return {
            'prediction': 'FAKE' if prediction == 1 else 'REAL',
            'confidence': max(probability),
            'fake_probability': probability[1],
            'real_probability': probability[0]
        }

if __name__ == "__main__":
    detector = FakeJobDetector()
    # List of all available datasets
    data_paths = [
        'data/enhanced_fake_jobs.csv',
        'data/sample_fake_jobs.csv',
        'fake_job_postings.csv'  # Your newly added dataset
    ]
    
    try:
        accuracy = detector.train(data_paths, advanced_training=True)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        # Fallback to existing datasets
        existing_paths = [path for path in data_paths[:-1] if os.path.exists(path)]
        if existing_paths:
            print("Falling back to existing datasets...")
            accuracy = detector.train(existing_paths, advanced_training=True)
        else:
            print("No valid datasets found. Please check your data directory.")
            accuracy = 0
    
    print(f"\nTraining completed with final accuracy: {accuracy:.4f}")