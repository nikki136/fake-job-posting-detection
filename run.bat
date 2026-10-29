@echo off
echo Fake Job Posting Detector
echo =======================

echo.
echo Installing dependencies...
python setup.py

echo.
echo Training model and starting application...
python train_and_run.py

pause