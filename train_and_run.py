#!/usr/bin/env python3
"""
Script to train the model and run the Flask application
"""
import os
import sys
import subprocess

def train_model():
    """Train the fake job detection model"""
    print("Training the fake job detection model...")
    try:
        # Import and run the training script
        from models.train_model import FakeJobDetector
        
        detector = FakeJobDetector()
        # List of all available datasets
        data_paths = [
            'data/enhanced_fake_jobs.csv',
            'data/sample_fake_jobs.csv',
            'data/fake_job_postings.csv'  # Your newly added dataset
        ]
        
        accuracy = detector.train(data_paths, advanced_training=True)
        
        print(f"Model training completed with accuracy: {accuracy:.4f}")
        return True
    except Exception as e:
        print(f"Error during model training: {str(e)}")
        return False

def run_app():
    """Run the Flask application"""
    print("Starting Flask application...")
    print("Access the application at: http://localhost:8000")
    
    # Import and run the Flask app directly instead of using subprocess
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=8000)
    except Exception as e:
        print(f"Error starting Flask application: {str(e)}")
        return False
    return True

if __name__ == "__main__":
    # First train the model
    if train_model():
        # Then run the Flask app
        run_app()
    else:
        print("Failed to train model. Exiting...")
        sys.exit(1)