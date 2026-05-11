import os
from functools import wraps

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def check_auth(username, password):
    """Check if a username/password combination is valid."""
    expected_user = os.environ.get("WEB_USERNAME", "admin")
    expected_pass = os.environ.get("WEB_PASSWORD")
    
    if not expected_pass:
        return True
        
    return username == expected_user and password == expected_pass

def authenticate():
    """Sends a 401 response that enables basic auth"""
    from flask import Response
    return Response(
    'Bitte loggen Sie sich ein.\n'
    'Zugriff verweigert.', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def create_app(test_config=None):
    from flask import Flask, request
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev"),
        DISCOGS_TOKEN=os.environ.get("DISCOGS_TOKEN"),
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Global Authentication Requirement
    @app.before_request
    def require_login():
        # Allow static files and skip auth if no password is configured
        if request.endpoint == 'static' or not os.environ.get("WEB_PASSWORD"):
            return
        
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()

    # Register Blueprints
    from .routes import picker, marketplace
    app.register_blueprint(picker.bp)
    app.register_blueprint(marketplace.bp)

    return app
