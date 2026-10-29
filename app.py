from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from functools import wraps
import sqlite3
import os
import sys
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple in-memory storage for tracking online users
# In a production environment, this would be stored in a database or cache
online_users = {}

# Clean up expired sessions periodically
def cleanup_expired_sessions():
    current_time = datetime.now()
    expired_users = [username for username, login_time in online_users.items() 
                     if current_time - login_time > timedelta(hours=24)]
    for username in expired_users:
        del online_users[username]

# Database setup
def init_db():
    """Initialize the database with a users table"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

from app.scraper import JobScraper
from app.predictor import JobPredictor

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'fake-job-detector-2024'
app.config['SESSION_TYPE'] = 'filesystem'

# Initialize the database
init_db()

# Create default admin user if it doesn't exist
def create_default_user():
    """Create a default admin user for demonstration purposes"""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        # Check if admin user exists
        c.execute("SELECT id FROM users WHERE username = ?", ("admin",))
        result = c.fetchone()
        
        # If no admin user exists, create one
        if not result:
            # Hash the default password 'password'
            default_password_hash = '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8'  # SHA-256 of 'password'
            c.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                      ("admin", "admin@example.com", default_password_hash))
            conn.commit()
            logger.info("Default admin user created")
        conn.close()
    except Exception as e:
        logger.error(f"Error creating default user: {str(e)}")

create_default_user()

# Enable CORS for all routes
CORS(app)

# Initialize components
scraper = JobScraper()
predictor = JobPredictor()

# Helper function to check if user is authenticated
def is_authenticated():
    return session.get('authenticated', False) and 'username' in session

# Decorator for requiring authentication
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/admin')
def admin_login():
    return render_template('admin_login.html')

@app.route('/api/admin/online-users')
def get_online_users():
    # In a real application, you would check if the user is an admin
    # For now, we'll return the list of online users
    cleanup_expired_sessions()  # Clean up expired sessions
    
    # Convert datetime objects to strings for JSON serialization
    users_list = []
    current_time = datetime.now()
    
    for username, login_time in online_users.items():
        users_list.append({
            'username': username,
            'login_time': login_time.isoformat(),
            'duration': str(current_time - login_time)
        })
    
    return jsonify({
        'count': len(users_list),
        'users': users_list
    })

@app.route('/api/admin/logout-user', methods=['POST'])
def admin_logout_user():
    # In a real application, you would check if the user is an admin
    data = request.get_json()
    username = data.get('username')
    
    if username in online_users:
        # Remove user from online list
        del online_users[username]
        return jsonify({'success': True, 'message': f'User {username} has been logged out'})
    else:
        return jsonify({'success': False, 'message': f'User {username} not found'}), 404

@app.route('/api/admin/database-users')
def get_database_users():
    # In a real application, you would check if the user is an admin
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT username, email, created_at FROM users ORDER BY created_at DESC")
        rows = c.fetchall()
        conn.close()
        
        users_list = []
        for row in rows:
            users_list.append({
                'username': row[0],
                'email': row[1],
                'created_at': row[2]
            })
        
        return jsonify({
            'count': len(users_list),
            'users': users_list
        })
    except Exception as e:
        logger.error(f"Error fetching database users: {str(e)}")
        return jsonify({'success': False, 'message': 'Error fetching users'}), 500

@app.route('/api/admin/delete-user', methods=['POST'])
def delete_user():
    # In a real application, you would check if the user is an admin
    data = request.get_json()
    username = data.get('username')
    
    if username == 'admin':
        return jsonify({'success': False, 'message': 'Cannot delete admin user'}), 400
    
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        conn.close()
        
        # Also remove from online users if present
        if username in online_users:
            del online_users[username]
            
        return jsonify({'success': True, 'message': f'User {username} has been deleted'})
    except Exception as e:
        logger.error(f"Error deleting user {username}: {str(e)}")
        return jsonify({'success': False, 'message': 'Error deleting user'}), 500

@app.route('/authenticate', methods=['POST'])
def authenticate():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Hash the provided password using SHA-256
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    # Check credentials against database
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT username FROM users WHERE username = ? AND password_hash = ?", 
                  (username, hashed_password))
        result = c.fetchone()
        conn.close()
        
        if result:
            session['authenticated'] = True
            session['username'] = username
            # Add CSRF protection token
            session['csrf_token'] = secrets.token_hex(16)
            # Track online user
            online_users[username] = datetime.now()
            return jsonify({'success': True, 'redirect': '/detection'})
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'})
    except Exception as e:
        logger.error(f"Database error during authentication: {str(e)}")
        return jsonify({'success': False, 'error': 'Authentication service unavailable'}), 500

@app.route('/logout')
def logout():
    # Remove user from online list
    if 'username' in session:
        online_users.pop(session['username'], None)
    session.clear()
    return redirect(url_for('login'))

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_user():
    # Try to get JSON data from request
    data = request.get_json()
    
    # If JSON data is not available, return an error
    if data is None:
        logger.error("No JSON data received in registration request")
        return jsonify({'success': False, 'error': 'Invalid request format. Please send JSON data.'}), 400
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    # Simple validation
    if not username or not email or not password:
        return jsonify({'success': False, 'error': 'All fields are required'}), 400
    
    # Hash the password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    # Store user in database
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                  (username, email, hashed_password))
        conn.commit()
        conn.close()
        
        # Auto-login after successful registration
        session['authenticated'] = True
        session['username'] = username
        # Add CSRF protection token
        session['csrf_token'] = secrets.token_hex(16)
        
        return jsonify({'success': True, 'message': 'Registration and login successful!', 'redirect': '/detection'})
    except sqlite3.IntegrityError as e:
        # Handle duplicate username or email
        if "username" in str(e).lower():
            return jsonify({'success': False, 'error': 'Username already exists'}), 400
        elif "email" in str(e).lower():
            return jsonify({'success': False, 'error': 'Email already registered'}), 400
        else:
            return jsonify({'success': False, 'error': 'Registration failed'}), 400
    except Exception as e:
        logger.error(f"Database error during registration: {str(e)}")
        logger.error(f"Exception type: {type(e)}")
        return jsonify({'success': False, 'error': 'Registration service unavailable'}), 500

@app.route('/user')
def get_user():
    if is_authenticated():
        return jsonify({'username': session['username']})
    else:
        return jsonify({'error': 'Not authenticated'}), 401

@app.route('/detection')
@login_required
def detection():
    return render_template('detection.html')

@app.route('/predict', methods=['POST', 'OPTIONS'])
def predict():
    if request.method == 'OPTIONS':
        # Handle preflight request
        return '', 200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    try:
        logger.info("Received prediction request")
        data = request.get_json()
        url = data.get('url', '').strip()
        text = data.get('text', '').strip()
        
        # Initialize is_fake_job_404 variable
        is_fake_job_404 = False
        
        logger.info(f"Request data - URL: {bool(url)}, Text: {bool(text)}")
        # Handle direct text input
        if text:
            logger.info("Processing direct text input")
            combined_text = text
        elif url:
            logger.info(f"Scraping job content from URL: {url}")
            
            # Validate URL appears to be a job posting (removed strict portal restriction)
            job_portals = ['linkedin.com', 'naukri.com', 'google.com/jobs', 'indeed.com', 'glassdoor.com', 'monster.com', 'ziprecruiter.com', 'careerbuilder.com']
            job_keywords = ['job', 'career', 'employment', 'position', 'opening', 'vacancy', 'work']
            
            # Check if URL is from known job portals or contains job keywords
            is_job_posting = (any(portal in url for portal in job_portals) or 
                             any(keyword in url.lower() for keyword in job_keywords))
            
            if not is_job_posting:
                logger.warning(f"URL does not appear to be a job posting: {url}")
                return jsonify({'error': 'This link does not appear to be a job posting. Please enter a valid job posting URL.'}), 200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
            
            # Scrape job content
            job_data = scraper.extract_job_content(url)
            
            # Check if this is an error
            if 'error' in job_data:
                logger.error(f"Error scraping URL {url}: {job_data['error']}")
                error_msg = job_data['error']
                # Provide more specific error messages
                if 'timeout' in error_msg.lower():
                    error_msg += '. This may happen if the website is slow or unreachable. Try pasting the job description directly instead.'
                elif 'connection' in error_msg.lower():
                    error_msg += '. Please check your internet connection or try a different job URL.'
                elif '404' in error_msg:
                    error_msg += ' The job posting may have been removed or the URL may be incorrect. Try pasting the job description directly instead.'
                elif '403' in error_msg:
                    error_msg += ' The website may be blocking automated access. Try pasting the job description directly instead.'
                return jsonify({'error': error_msg}), 200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
            
            # For 404 cases that return fake job data instead of errors
            is_fake_job_404 = job_data.get('title') == 'Job Not Found'
            if is_fake_job_404:
                logger.info(f"Job not found for URL {url}, treating as fake job")
            
            # Get combined text for prediction
            combined_text = scraper.get_combined_text(job_data)
            logger.info(f"Successfully scraped content from {url}")
        else:
            return jsonify({'error': 'Please provide either a URL or job text'}), 200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
        
        if not combined_text.strip():
            logger.warning("No content found to analyze")
            return jsonify({'error': 'No content found to analyze'}), 200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
        
        # Make prediction
        logger.info("Making prediction with model")
        result = predictor.predict(combined_text, url)
        
        # For 404 jobs, force them to be marked as fake
        if is_fake_job_404:
            result['prediction'] = 'FAKE'
            result['confidence'] = 95  # High confidence for 404s
            result['fake_probability'] = 95
            result['real_probability'] = 5
            result['explanation'] = 'This job posting could not be found. The URL may be invalid or the job posting may have been removed. Job postings that cannot be verified are typically fraudulent.'
            # Still populate job details with what we have
            if not text:
                result['job_details'] = {
                    'title': job_data.get('title', 'Not found'),
                    'company': job_data.get('company', 'Not found'),
                    'location': job_data.get('location', 'Not found'),
                    'posted_date': job_data.get('posted_date', ''),
                    'url': url
                }
        
        logger.info(f"Prediction result: {result.get('prediction', 'UNKNOWN')} with confidence {result.get('confidence', 0)}%")
        
        # Add job details to result
        if text:
            result['job_details'] = {
                'title': 'Provided Text',
                'company': 'N/A',
                'location': 'N/A',
                'url': 'Text Input'
            }
        else:
            # Check if we already populated job details for 404 cases
            if 'job_details' not in result:
                result['job_details'] = {
                    'title': job_data.get('title', 'Not found'),
                    'company': job_data.get('company', 'Not found'),
                    'location': job_data.get('location', 'Not found'),
                    'posted_date': job_data.get('posted_date', ''),
                    'url': url
                }
        
        logger.info("Returning successful prediction result")
        return jsonify(result), 200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
        
    except Exception as e:
        logger.error(f"Server error in prediction: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500, {'Access-Control-Allow-Origin': '*'}

@app.route('/model-info')
def model_info():
    logger.info("Model info endpoint accessed")
    info = predictor.get_model_info()
    logger.info(f"Model info: {info}")
    return jsonify(info)

@app.route('/health')
def health_check():
    logger.info("Health check endpoint accessed")
    return jsonify({'status': 'healthy', 'message': 'Server is running properly'})

@app.route('/test-url', methods=['POST'])
def test_url():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
        
        logger.info(f"Testing URL accessibility: {url}")
        
        # Test URL accessibility
        status_code = scraper.test_url_accessibility(url)
        
        if status_code is None:
            return jsonify({'error': 'Could not test URL accessibility', 'url': url}), 500
        elif status_code == 200:
            return jsonify({'status': 'accessible', 'message': 'URL is accessible', 'url': url, 'status_code': status_code}), 200
        elif status_code == 404:
            return jsonify({'status': 'not_found', 'message': 'URL not found (404)', 'url': url, 'status_code': status_code}), 200
        elif status_code == 403:
            return jsonify({'status': 'forbidden', 'message': 'Access forbidden (403)', 'url': url, 'status_code': status_code}), 200
        elif status_code >= 400:
            return jsonify({'status': 'error', 'message': f'HTTP error {status_code}', 'url': url, 'status_code': status_code}), 200
        else:
            return jsonify({'status': 'unknown', 'message': f'URL returned status code {status_code}', 'url': url, 'status_code': status_code}), 200
            
    except Exception as e:
        logger.error(f"Error testing URL: {str(e)}")
        return jsonify({'error': f'Error testing URL: {str(e)}'}), 500

if __name__ == '__main__':
    logger.info("Starting Fake Job Detection application")
    logger.info(f"Model loaded: {predictor.model is not None}")
    logger.info(f"Vectorizer loaded: {predictor.vectorizer is not None}")
    app.run(debug=True, host='0.0.0.0', port=8000)
