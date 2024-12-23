from flask import send_from_directory, send_file
import logging
import os

logger = logging.getLogger(__name__)

def init_static_routes(app, STATIC_DIR):
    @app.route('/')
    def serve_index():
        try:
            index_path = os.path.join(STATIC_DIR, 'index.html')
            if os.path.exists(index_path):
                logger.info(f"Serving index.html from {index_path}")
                return send_file(index_path)
            else:
                logger.error(f"index.html not found at {index_path}")
                return "Error: index.html not found", 404
        except Exception as e:
            logger.error(f"Error serving index.html: {str(e)}")
            return f"Error: Could not serve index.html", 404

    @app.route('/static/<path:filename>')
    def serve_static(filename):
        try:
            logger.info(f"Attempting to serve static file: {filename}")
            return send_from_directory(STATIC_DIR, filename)
        except Exception as e:
            logger.error(f"Error serving static file {filename}: {str(e)}")
            return f"Error: Could not find {filename}", 404

    @app.route('/style.css')
    def serve_css():
        try:
            css_path = os.path.join(STATIC_DIR, 'style.css')
            if os.path.exists(css_path):
                logger.info(f"Serving style.css from {css_path}")
                return send_file(css_path, mimetype='text/css')
            else:
                logger.error(f"style.css not found at {css_path}")
                return "Error: style.css not found", 404
        except Exception as e:
            logger.error(f"Error serving style.css: {str(e)}")
            return "Error: Could not serve style.css", 404

    @app.route('/favicon.ico')
    def serve_favicon():
        try:
            favicon_path = os.path.join(STATIC_DIR, 'favicon.ico')
            if os.path.exists(favicon_path):
                return send_file(favicon_path, mimetype='image/x-icon')
            else:
                return '', 204  # No content response if favicon doesn't exist
        except Exception as e:
            logger.error(f"Error serving favicon.ico: {str(e)}")
            return '', 204