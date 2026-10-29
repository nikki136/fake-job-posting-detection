#!/usr/bin/env python3
"""
Setup script to install dependencies and prepare the environment
"""
import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("All packages installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        return False
    return True

def check_installation():
    """Check if packages are installed correctly"""
    print("Checking installation...")
    try:
        import flask, sklearn, pandas, requests, bs4, joblib
        print("All packages installed successfully!")
        return True
    except ImportError as e:
        print(f"Missing package: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ['models', 'data', 'static/css', 'templates', 'app']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print("Directories created successfully!")

if __name__ == "__main__":
    print("Setting up Fake Job Posting Detector...")
    
    create_directories()
    
    if install_requirements():
        if check_installation():
            print("\nSetup completed successfully!")
            print("Run 'python train_and_run.py' to start the application.")
        else:
            print("\nSetup completed with warnings.")
    else:
        print("\nSetup failed.")