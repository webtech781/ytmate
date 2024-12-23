from flask import Flask, render_template, request
from flask_cors import CORS
import logging
import os
import tempfile
import threading
import time
from routes.url_routes import init_routes
from routes.static_routes import init_static_routes

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get the absolute paths
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
logger.info(f"Static directory path: {STATIC_DIR}")
logger.info(f"Template directory path: {TEMPLATE_DIR}")

app = Flask(__name__, 
           static_folder=STATIC_DIR,
           template_folder=TEMPLATE_DIR)
CORS(app)

# Create a temporary directory for processing
TEMP_DIR = tempfile.mkdtemp()
logger.info(f"Created temporary directory: {TEMP_DIR}")

def cleanup_temp_file(filepath, delay=300):
    """Delete temporary file after specified delay"""
    def delete_file():
        time.sleep(delay)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Deleted temporary file: {filepath}")
        except Exception as e:
            logger.error(f"Error deleting temporary file: {str(e)}")

    thread = threading.Thread(target=delete_file)
    thread.daemon = True
    thread.start()

# Add cleanup_temp_file to app context
app.cleanup_temp_file = cleanup_temp_file

# Ensure directories exist
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)
    logger.info(f"Created static directory: {STATIC_DIR}")

if not os.path.exists(TEMPLATE_DIR):
    os.makedirs(TEMPLATE_DIR)
    logger.info(f"Created templates directory: {TEMPLATE_DIR}")

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    error_message = "The requested page was not found. Please check the URL and try again."
    return render_template('error.html', error_message=error_message), 404

@app.errorhandler(500)
def internal_error(e):
    error_message = "An internal server error occurred. Please try again later."
    return render_template('error.html', error_message=error_message), 500

@app.route('/error')
def error_page():
    error_message = request.args.get('message', 'An error occurred while processing your request.')
    return render_template('error.html', error_message=error_message)

# Initialize routes
init_static_routes(app, STATIC_DIR)  # Initialize static file routes
init_routes(app, TEMP_DIR)  # Initialize API routes

if __name__ == '__main__':
    # List files in static directory
    if os.path.exists(STATIC_DIR):
        files = os.listdir(STATIC_DIR)
        logger.info(f"Files in static directory: {files}")
    
    if os.path.exists(TEMPLATE_DIR):
        files = os.listdir(TEMPLATE_DIR)
        logger.info(f"Files in templates directory: {files}")
    
    app.run(host='0.0.0.0', debug=False, port=5000)