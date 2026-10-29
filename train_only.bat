@echo off
echo Fake Job Posting Detector - Training Only
echo ======================================

echo.
echo Training the model...
echo ------------------
python -c "from models.train_model import FakeJobDetector; detector = FakeJobDetector(); detector.train(['data/enhanced_fake_jobs.csv', 'data/sample_fake_jobs.csv', 'data/fake_job_postings.csv'], advanced_training=True)"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Model training completed successfully!
) else (
    echo.
    echo Error: Model training failed.
)

pause