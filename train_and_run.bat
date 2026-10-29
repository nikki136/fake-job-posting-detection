@echo off
echo Fake Job Posting Detector - Train and Run Script
echo =================================================

echo.
echo Step 1: Training the model...
echo -------------------------------
python -c "from models.train_model import FakeJobDetector; detector = FakeJobDetector(); detector.train(['data/enhanced_fake_jobs.csv', 'data/sample_fake_jobs.csv', 'data/fake_job_postings.csv'], advanced_training=True)"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Step 2: Starting Flask application...
    echo -----------------------------------
    python app.py
) else (
    echo.
    echo Error: Model training failed. Flask server will not start.
    pause
    exit /b 1
)

pause