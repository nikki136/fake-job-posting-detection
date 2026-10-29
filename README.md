# Fake Job Posting Detector

A machine learning-based tool to detect fraudulent job postings using Natural Language Processing and Logistic Regression.

## Overview

The Fake Job Posting Detector is an intelligent system designed to help job seekers identify potentially fraudulent job postings. By analyzing the content and characteristics of job postings, the system can accurately classify them as legitimate or fake with detailed explanations for its decisions.

This tool is particularly valuable in today's job market, where scams and fraudulent job postings are increasingly common. The system provides both automated analysis of job posting URLs and manual text analysis for maximum flexibility.

## Key Benefits

- **Protect Job Seekers**: Identify potentially fraudulent job postings before applying
- **Save Time**: Quickly analyze job postings without manual review
- **Detailed Insights**: Understand why a job posting was flagged as fake
- **Easy to Use**: Simple web interface for quick analysis
- **Extensible**: Easy to train with custom datasets for improved accuracy

## Features
- Detects fake job postings with high accuracy using machine learning
- Uses TF-IDF vectorization and Logistic Regression algorithms
- Web interface built with Flask for easy access
- Easy to train with custom datasets
- Supports job posting analysis from LinkedIn and other major job boards
- Extracts and displays job title, company name, location, and posting date
- Provides detailed explanations for fake job detections
- Handles network errors and provides user-friendly error messages
- Supports manual text analysis when URL scraping fails
- Cross-platform compatibility (Windows, macOS, Linux)
- Batch processing scripts for easy setup and execution
- Comprehensive logging for troubleshooting

## Prerequisites
- Python 3.6 or higher
- pip package manager

## System Requirements

- **Operating System**: Windows, macOS, or Linux
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: 500MB free space for installation and datasets
- **Internet Connection**: Required for job posting analysis and package installation

## Recommended: Virtual Environment

It's recommended to use a virtual environment to avoid conflicts with other Python projects:

**Windows:**
```
python -m venv fakejob_env
fakejob_env\Scripts\activate
```

**macOS/Linux:**
```
python3 -m venv fakejob_env
source fakejob_env/bin/activate
```

After activating the virtual environment, proceed with the installation steps below.

## Required Python Packages

The application requires the following Python packages, which are listed in the `requirements.txt` file:

| Package | Version | Description |
|---------|---------|-------------|
| Flask | >=2.0.0 | Web framework for the application |
| flask-cors | >=3.0.0 | Cross-Origin Resource Sharing support |
| scikit-learn | >=1.0.0 | Machine learning library |
| pandas | >=1.3.0 | Data manipulation and analysis |
| numpy | >=1.21.0 | Numerical computing |
| requests | >=2.25.0 | HTTP library for web requests |
| beautifulsoup4 | >=4.9.0 | HTML parsing for web scraping |
| joblib | >=1.0.0 | Library for serialization |

These packages will be automatically installed when you run the setup script or install from requirements.txt.

## Installation

1. Clone or download this repository
2. Navigate to the project directory

### Automatic Installation

You can automatically install all dependencies using either of these methods:

**Option 1: Using pip directly**
```
pip install -r requirements.txt
```

This will install all the required Python packages listed in the requirements.txt file:
- Flask - Web framework for the application
- flask-cors - Cross-Origin Resource Sharing support
- scikit-learn - Machine learning library
- pandas - Data manipulation and analysis
- numpy - Numerical computing
- requests - HTTP library for web requests
- beautifulsoup4 - HTML parsing for web scraping
- joblib - Library for serialization

**Option 2: Using the setup script**
```
python setup.py
```

This will:
- Install all required dependencies
- Create necessary directories
- Verify the installation

### Manual Installation

If you prefer to install packages manually, you can install each dependency individually:
```
pip install Flask flask-cors scikit-learn pandas numpy requests beautifulsoup4 joblib
```

### Updating Dependencies

To update all dependencies to their latest versions, you can run:
```
pip install --upgrade -r requirements.txt
```

This will upgrade all packages to their latest compatible versions as specified in the requirements.txt file.

### Common Installation Issues

1. **Permission Errors**: On some systems, you might encounter permission errors when installing packages. Try using:
   ```
   pip install --user -r requirements.txt
   ```

2. **SSL Certificate Errors**: If you encounter SSL certificate errors, you can try:
   ```
   pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
   ```

3. **Package Conflicts**: If you have package conflicts, consider using a virtual environment as described above.

4. **Outdated pip**: If you have an outdated version of pip, update it first:
   ```
   python -m pip install --upgrade pip
   ```

### Verifying Installation

To verify that all dependencies have been installed correctly, you can run:
```
python setup.py
```

This script will check if all required packages are properly installed and notify you of any missing dependencies.

You can also manually verify the installation by running:
```
python -c "import flask, sklearn, pandas, numpy, requests, bs4, joblib, flask_cors; print('All packages installed successfully!')"
```

If any package is missing, you'll see an ImportError. In that case, run `pip install -r requirements.txt` to install all required packages.

### Quick Setup with Batch Script

On Windows, you can quickly set up and run the application using the provided batch script:
```
run.bat
```

This script will automatically install dependencies, train the model, and start the application.

## Dataset

The system uses CSV files containing job posting data with the following columns:
- job_id
- title
- location
- department
- company_profile
- description
- requirements
- benefits
- employment_type
- required_experience
- required_education
- industry
- function
- fraudulent (target variable: 0 for legitimate, 1 for fake)

### Sample Datasets

The project includes sample datasets in the `data/` directory:
- `enhanced_fake_jobs.csv` - Enhanced dataset with additional features
- `sample_fake_jobs.csv` - Sample dataset for testing
- `fake_job_postings.csv` - Main dataset file

### Adding Your Own Dataset

To use your own dataset:
1. Ensure it follows the same column structure as the sample datasets
2. Place it in the `data/` directory
3. The system will automatically load all CSV files in the `data/` directory during training

### Dataset Quality

For best results:
- Ensure your dataset contains a balanced mix of legitimate and fake job postings
- Include diverse job types and industries
- Provide complete information for each job posting
- Clean the data to remove duplicates and irrelevant entries

## Training the Model

To train the model with the provided datasets:
```
python train_and_run.py
```

This command will:
1. Load all datasets from the `data/` directory
2. Preprocess the text data
3. Train the machine learning model
4. Save the trained model and vectorizer
5. Start the Flask web server

Alternatively, if you want to only train the model without starting the server:
```
python models/train_model.py
```

### Machine Learning Approach

The system uses a combination of Natural Language Processing and machine learning techniques:

1. **Text Preprocessing**: Job posting text is cleaned and normalized
2. **Feature Extraction**: TF-IDF (Term Frequency-Inverse Document Frequency) vectorization converts text to numerical features
3. **Classification**: Logistic Regression algorithm classifies job postings as legitimate or fake
4. **Model Evaluation**: The system evaluates model performance using accuracy metrics

### Model Performance

The model achieves high accuracy in detecting fake job postings through:
- Analysis of job title, description, and requirements
- Detection of suspicious patterns and phrases
- Comparison with known legitimate job characteristics

### Retraining the Model

To retrain the model with updated data:
1. Add new dataset files to the `data/` directory
2. Run `python train_and_run.py` to retrain with all available data
3. The new model will overwrite the previous one in the `models/` directory

## Running the Application

After training, the Flask server will automatically start and be accessible at:
http://localhost:8000

### Running Methods

You can run the application in several ways depending on your needs:

**Method 1: Direct Python execution**
```
python app.py
```
This method runs the Flask server directly without retraining the model. Use this method when you've already trained the model and just want to start the web interface.

**Method 2: Train and run in one command**
```
python train_and_run.py
```
This method trains the model and then starts the Flask server. Use this method when you want to retrain the model with new data before starting the application.

### Using Batch Scripts (Windows)

For easier execution, the project includes several batch scripts:

- `run.bat` - Installs dependencies, trains the model, and starts the Flask server (recommended for first-time use)
- `train_and_run.bat` - Trains the model and starts the Flask server
- `train_only.bat` - Only trains the model without starting the server
- `run_server.bat` - Runs the Flask server without retraining the model

To use any of these scripts, simply double-click on them or run them from the command prompt:
```
run.bat
```

### Accessing the Application

Once the server is running, open your web browser and navigate to:
- http://localhost:8000 - Main landing page
- http://localhost:8000/detection - Job detection interface

The application will continue running until you close the terminal/command prompt window or press Ctrl+C.

### Using the Job Detection Feature

To analyze a job posting:
1. Navigate to the detection page (http://localhost:8000/detection)
2. Enter a job posting URL from LinkedIn or other supported job boards
3. Click "Analyze URL" to check if the job is legitimate or potentially fraudulent
4. The system will display the job title, company name, location, and posting date along with the analysis results
5. For fake job detections, detailed explanations of why the job was flagged will be provided

### Job Posting Analysis Process

The system analyzes job postings through the following steps:

1. **URL Validation**: Checks if the URL is from a supported job board
2. **Web Scraping**: Extracts job posting content from the URL
3. **Information Extraction**: Identifies job title, company name, location, and posting date
4. **Text Analysis**: Processes the job posting text for machine learning analysis
5. **Fraud Detection**: Applies the trained model to classify the job posting
6. **Result Presentation**: Displays analysis results with confidence scores and explanations

### Supported Job Boards

The system currently supports job postings from:
- LinkedIn
- Naukri
- Other major job boards (with varying degrees of support)

### Manual Text Analysis

If URL analysis fails, you can paste the job description directly:
1. Click the "Paste Text" tab on the detection page
2. Copy and paste the job description into the text area
3. Click "Analyze Text" to perform the analysis

This method bypasses web scraping and directly analyzes the provided text.

### Stopping the Application

To stop the Flask server:
1. Go to the terminal/command prompt window where the server is running
2. Press `Ctrl+C` to gracefully shut down the server

On Windows, if you started the application using a batch script, you can also close the command prompt window directly.

### Web Interface

The application provides two main pages:
1. Landing page - Introduction to the system
2. Detection page - Tool for checking job postings

## Adding Custom Datasets

To add your own dataset:
1. Place your CSV file in the `data/` directory
2. Ensure it has the same column structure as the sample datasets
3. Run the training command again:
   ```
   python train_and_run.py
   ```

## Troubleshooting

### "No columns to parse from file" Error
If you encounter this error, it means one of your CSV files in the `data/` directory is empty or corrupted:
1. Check that your CSV files are not empty
2. Verify that they contain proper column headers
3. Ensure files are in the correct CSV format

To fix this issue:
```
# Copy a valid dataset file to replace the empty one
copy "source_file.csv" "data\fake_job_postings.csv"
```

If you don't have any dataset files, you can start by copying one of the sample files:
```
copy "data\sample_fake_jobs.csv" "data\fake_job_postings.csv"
```

### Model Training Issues
If the model fails to train:
1. Ensure all required packages are installed by running `python setup.py`
2. Check that your dataset files contain valid data
3. Verify that your CSV files have the required columns

### Common Issues and Solutions

1. **Missing Dependencies**: If you get import errors, run `python setup.py` to install all required packages.

2. **Port Already in Use**: If the Flask server fails to start because port 8000 is in use, you can modify the port in `app.py`.

3. **Empty Dataset Files**: Ensure all CSV files in the `data/` directory contain actual data with proper headers.

4. **Insufficient Training Data**: The model performs better with larger datasets. Consider adding more data to improve accuracy.

5. **Network Connectivity Issues**: If you're having trouble analyzing job posting URLs, check your internet connection and ensure the job posting URL is accessible in your browser.

6. **Job Analysis Failures**: If job analysis fails with "Text content is too short for analysis", try pasting the job description directly instead of using a URL.

### Batch Script Issues

If the batch scripts are not working:
1. Ensure you're running them from the project root directory
2. Check that Python is properly installed and added to your PATH
3. Verify that all required dependencies are installed by running `pip install -r requirements.txt`

### Job Analysis Troubleshooting

If job analysis is failing:
1. **URL Issues**: Ensure the job posting URL is valid and accessible in your browser
2. **Short Content**: Some job postings may have very little text content. Try pasting the job description directly
3. **Unsupported Platforms**: The system primarily supports LinkedIn and Naukri job postings. Other platforms may have limited support
4. **Network Errors**: Check your internet connection and try again
5. **Blocked Access**: Some websites may block automated access. Try accessing the URL manually first

## Project Structure

```
├── app/                    # Flask application modules
│   ├── __init__.py
│   ├── predictor.py        # ML prediction logic
│   └── scraper.py          # Web scraping functionality
├── data/                   # Dataset files
│   ├── enhanced_fake_jobs.csv
│   ├── sample_fake_jobs.csv
│   └── fake_job_postings.csv
├── models/                 # Machine learning model files
│   └── train_model.py      # Model training implementation
├── static/                 # CSS and other static assets
├── templates/              # HTML template files
├── requirements.txt        # Python package dependencies
├── setup.py                # Environment setup script
├── app.py                  # Main Flask application
├── train_and_run.py        # Main training and execution script
├── run.bat                 # Windows batch script to run the application
├── train_and_run.bat       # Windows batch script to train and run
├── train_only.bat          # Windows batch script to only train the model
└── run_server.bat          # Windows batch script to run the server only
```

## Technology Stack

- **Backend**: Python 3.6+, Flask
- **Machine Learning**: Scikit-learn, Logistic Regression, TF-IDF Vectorization
- **Data Processing**: Pandas, NumPy
- **Web Scraping**: BeautifulSoup4, Requests
- **Frontend**: HTML, CSS, JavaScript
- **Data Storage**: CSV files
- **Model Serialization**: Joblib
- **Cross-Origin Support**: Flask-CORS

## Contributing

Contributions to improve the Fake Job Posting Detector are welcome! Here are ways you can contribute:

1. **Bug Reports**: Report issues you encounter
2. **Feature Requests**: Suggest new features or improvements
3. **Code Contributions**: Submit pull requests with bug fixes or new features
4. **Dataset Improvements**: Contribute better training datasets
5. **Documentation**: Help improve this documentation

### Getting Started with Development

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Development Guidelines

- Follow PEP 8 coding standards
- Write clear, commented code
- Test your changes before submitting
- Update documentation as needed

## Support

If you need help with the Fake Job Posting Detector:

1. **Check the Documentation**: Review this README and other documentation files
2. **Review Issues**: Check the GitHub issues page for similar problems
3. **Contact**: For support requests, please open an issue on the project repository

### Reporting Issues

When reporting issues, please include:
- Steps to reproduce the problem
- Error messages you're seeing
- Your operating system and Python version
- Screenshots if applicable

## License

This project is licensed under the MIT License.