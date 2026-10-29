import joblib
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

class JobPredictor:
    def __init__(self, model_path='models/fake_job_model.pkl', vectorizer_path='models/tfidf_vectorizer.pkl'):
        self.model_path = model_path
        self.vectorizer_path = vectorizer_path
        self.model = None
        self.vectorizer = None
        self.load_model()
    
    def load_model(self):
        """Load the trained model and vectorizer"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.vectorizer_path):
                self.model = joblib.load(self.model_path)
                self.vectorizer = joblib.load(self.vectorizer_path)
                print("Model and vectorizer loaded successfully!")
            else:
                print("Model files not found. Please train the model first.")
                return False
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            return False
        return True
    
    def preprocess_text(self, text):
        """Clean and preprocess text data"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = str(text).lower()
        
        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def predict(self, text, url=None):
        """Predict if a job posting is fake or real"""
        if not self.model or not self.vectorizer:
            return {
                'error': 'Model not loaded. Please ensure the application has been properly trained. Run the training process first using the train_and_run.py script.',
                'prediction': 'UNKNOWN',
                'confidence': 0.0
            }
        
        try:
            # Preprocess the text
            processed_text = self.preprocess_text(text)
            
            if not processed_text.strip():
                return {
                    'error': 'No valid text content found for analysis',
                    'prediction': 'UNKNOWN',
                    'confidence': 0.0
                }
            
            # Check if text is too short for meaningful analysis
            # Special handling for Google job links - allow shorter content
            words = processed_text.split()
            if len(words) < 10:
                # For Google jobs, allow as few as 5 words
                if url and 'google.com' in url and len(words) >= 5:
                    # Continue with analysis for Google jobs with at least 5 words
                    pass
                else:
                    return {
                        'error': 'Text content is too short for analysis. Please provide more detailed job information.',
                        'prediction': 'UNKNOWN',
                        'confidence': 0.0
                    }
            
            # Vectorize the text
            text_tfidf = self.vectorizer.transform([processed_text])
            
            # Make prediction
            prediction = self.model.predict(text_tfidf)[0]
            probabilities = self.model.predict_proba(text_tfidf)[0]
            
            # Calculate confidence and result
            confidence = max(probabilities)
            result = 'FAKE' if prediction == 1 else 'REAL'
            
            # Generate explanation based on prediction
            explanation = self._generate_explanation(result, processed_text, probabilities)
            
            return {
                'prediction': result,
                'confidence': round(confidence * 100, 2),
                'fake_probability': round(probabilities[1] * 100, 2),
                'real_probability': round(probabilities[0] * 100, 2),
                'processed_text_length': len(processed_text.split()),
                'explanation': explanation
            }
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return {
                'error': f'Prediction error: {str(e)}',
                'prediction': 'UNKNOWN',
                'confidence': 0.0
            }
    
    def _generate_explanation(self, prediction, text, probabilities):
        """Generate explanation for why a job was classified as fake or real"""
        # Common red flags for fake jobs
        fake_patterns = [
            (r'work from home|work-at-home|remote work', 'Work from home offers (often unrealistic)'),
            (r'no (experience|skills|education) required', 'No qualifications required'),
            (r'(easy|quick) money', 'Promises of easy/quick money'),
            (r'\$[0-9]+(?:,[0-9]+)?\s*(?:per hour|hourly|weekly|monthly)', 'Unrealistically high pay claims'),
            (r'send money|pay upfront|processing fee|deposit', 'Requires upfront payment'),
            (r'guaranteed.*income|unlimited.*earnings', 'Guaranteed income promises'),
            (r'immediate start|start today|no interview', 'No interview process'),
            (r'no diploma|required|high school', 'Minimal education requirements'),
            (r'get rich|millionaire|financial freedom', 'Get rich quick schemes'),
            (r'opportunity of (a )?lifetime', 'Opportunity of a lifetime claims')
        ]
        
        # Common indicators of legitimate jobs
        real_patterns = [
            (r'(job )?requirements?', 'Clear job requirements'),
            (r'qualifications?', 'Qualification requirements'),
            (r'(years of )?experience', 'Experience requirements'),
            (r'(bachelor|master|degree)', 'Educational requirements'),
            (r'skills', 'Skills requirements'),
            (r'benefits', 'Employee benefits'),
            (r'(health )?insurance', 'Health insurance benefits'),
            (r'paid (time|vacation)|pto', 'Paid time off'),
            (r'interview process|application process', 'Formal hiring process'),
            (r'equal opportunity', 'Equal opportunity employer'),
            (r'professional development|career growth', 'Career development'),
            (r'team collaboration|team environment', 'Team-based work')
        ]
        
        # Find matching patterns
        fake_matches = []
        for pattern, description in fake_patterns:
            if re.search(pattern, text.lower()):
                fake_matches.append(description)
        
        real_matches = []
        for pattern, description in real_patterns:
            if re.search(pattern, text.lower()):
                real_matches.append(description)
        
        # Generate explanation based on prediction
        if prediction == 'FAKE':
            explanation = "This job posting has been flagged as potentially fraudulent based on our analysis.\n\n"
            
            if len(fake_matches) > 0:
                explanation += f"Red flags detected:\n• {"\n• ".join(list(set(fake_matches))[:5])}\n\n"
            
            # Confidence level explanation
            if probabilities[1] > 0.9:  # Very high confidence fake
                explanation += "The system is very highly confident (90%+) this is a fake job posting."
            elif probabilities[1] > 0.8:  # High confidence fake
                explanation += "The system is highly confident (80-90%) this is a fake job posting."
            elif probabilities[1] > 0.7:  # Medium-high confidence fake
                explanation += "The system is moderately confident (70-80%) this is a fake job posting."
            elif probabilities[1] > 0.6:  # Medium confidence fake
                explanation += "The system has some concerns (60-70%) this is a fake job posting."
            else:  # Lower confidence fake
                explanation += "The system has detected some suspicious elements in this job posting."
                
        else:  # REAL
            explanation = "This job posting appears to be legitimate based on our analysis.\n\n"
            
            if len(real_matches) > 0:
                explanation += f"Positive indicators:\n• {"\n• ".join(list(set(real_matches))[:5])}\n\n"
            
            # Confidence level explanation
            if probabilities[0] > 0.9:  # Very high confidence real
                explanation += "The system is very highly confident (90%+) this is a legitimate job posting."
            elif probabilities[0] > 0.8:  # High confidence real
                explanation += "The system is highly confident (80-90%) this is a legitimate job posting."
            elif probabilities[0] > 0.7:  # Medium-high confidence real
                explanation += "The system is moderately confident (70-80%) this is a legitimate job posting."
            elif probabilities[0] > 0.6:  # Medium confidence real
                explanation += "The system is somewhat confident (60-70%) this is a legitimate job posting."
            else:  # Lower confidence real
                explanation += "The system has not found strong evidence that this is a fake job posting."
        
        return explanation.strip()
    
    def get_model_info(self):
        """Get information about the loaded model"""
        if not self.model or not self.vectorizer:
            return {'status': 'Model not loaded'}
        
        return {
            'status': 'Model loaded',
            'model_type': type(self.model).__name__,
            'vectorizer_type': type(self.vectorizer).__name__,
            'feature_count': len(self.vectorizer.get_feature_names_out()) if hasattr(self.vectorizer, 'get_feature_names_out') else 'Unknown'
        }