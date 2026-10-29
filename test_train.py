from models.train_model import FakeJobDetector
import os

if __name__ == "__main__":
    print("Training model with all available datasets...")
    detector = FakeJobDetector()
    try:
        # List of all available datasets
        data_paths = [
            'data/enhanced_fake_jobs.csv',
            'data/sample_fake_jobs.csv',
            'fake_job_postings.csv'  # Your newly added dataset
        ]
        
        # Filter to only existing files
        existing_paths = [path for path in data_paths if os.path.exists(path)]
        
        if existing_paths:
            accuracy = detector.train(existing_paths, advanced_training=True)
            print(f"Training completed with accuracy: {accuracy:.4f}")
        else:
            print("No valid datasets found. Please check your data directory.")
    except Exception as e:
        print(f"Error during training: {e}")
        import traceback
        traceback.print_exc()