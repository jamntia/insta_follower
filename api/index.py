from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
import os
import sys
import traceback
from dotenv import load_dotenv
from instagrapi import Client
import json
import tempfile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Get secret key from environment variable or use a default for development
app.secret_key = os.getenv('SECRET_KEY', 'dev-key-change-this')
load_dotenv()

# Simple rate limiting
RATE_LIMIT_MINUTES = 5
MAX_REQUESTS_PER_IP = 3
ip_request_counts = defaultdict(list)

def rate_limit():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = request.remote_addr
            now = datetime.now()
            
            # Remove old requests
            ip_request_counts[ip] = [
                timestamp for timestamp in ip_request_counts[ip]
                if timestamp > now - timedelta(minutes=RATE_LIMIT_MINUTES)
            ]
            
            # Check if rate limit is exceeded
            if len(ip_request_counts[ip]) >= MAX_REQUESTS_PER_IP:
                flash('Rate limit exceeded. Please try again later.', 'error')
                return redirect(url_for('index'))
            
            # Add current request
            ip_request_counts[ip].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

class LoginForm(FlaskForm):
    username = StringField('Instagram Username', validators=[DataRequired()])
    password = PasswordField('Instagram Password', validators=[DataRequired()])
    submit = SubmitField('Analyze Followers')

def setup_instagram_client():
    """Setup Instagram client with default settings"""
    try:
        cl = Client()
        cl.settings = {
            "uuids": {},
            "cookies": {},
            "device_settings": {},
            "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 239.2.0.17.109 (iPhone13,3; iOS 15_5; en_US; en-US; scale=3.00; 1170x2532; 376668393)"
        }
        return cl
    except Exception as e:
        logger.error(f"Error setting up Instagram client: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def get_instagram_data(username, password):
    """Get Instagram follower data with comprehensive error handling"""
    logger.info("Starting Instagram data retrieval")
    try:
        cl = setup_instagram_client()
        logger.info("Instagram client setup complete")

        # Attempt login
        logger.info("Attempting Instagram login")
        cl.login(username, password)
        logger.info("Login successful")
        
        user_id = cl.user_id
        logger.info(f"Retrieved user ID: {user_id}")

        # Get followers and following
        logger.info("Fetching followers")
        followers = cl.user_followers(user_id)
        logger.info(f"Found {len(followers)} followers")
        
        logger.info("Fetching following")
        following = cl.user_following(user_id)
        logger.info(f"Found {len(following)} following")

        # Process the data
        non_followers = {
            str(user_id): {
                "username": user_info.username,
                "full_name": user_info.full_name,
                "profile_pic_url": user_info.profile_pic_url
            }
            for user_id, user_info in following.items()
            if user_id not in followers
        }
        
        logger.info(f"Analysis complete. Found {len(non_followers)} non-followers")
        return {
            "success": True,
            "data": non_followers,
            "total": len(non_followers)
        }
    except Exception as e:
        error_msg = f"Error in get_instagram_data: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": error_msg
        }

@app.route('/', methods=['GET', 'POST'])
def index():
    """Main route handler with error handling"""
    try:
        form = LoginForm()
        if form.validate_on_submit():
            logger.info("Form submitted, processing Instagram data")
            result = get_instagram_data(form.username.data, form.password.data)
            if result["success"]:
                return render_template(
                    'results.html',
                    non_followers=result["data"],
                    total=result["total"]
                )
            else:
                flash(f'Error: {result["error"]}', 'error')
                return redirect(url_for('index'))
        return render_template('index.html', form=form)
    except Exception as e:
        error_msg = f"Unexpected error in index route: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        flash(error_msg, 'error')
        return render_template('index.html', form=LoginForm())

@app.route('/health')
def health_check():
    """Health check endpoint for debugging"""
    return jsonify({
        "status": "healthy",
        "python_version": sys.version,
        "environment": os.environ.get('FLASK_ENV', 'production')
    })

# Handle favicon.ico
app.add_url_rule('/favicon.ico', redirect_to=url_for('static', filename='favicon.ico'))

# For local development
if __name__ == '__main__':
    app.run(debug=True) 