import os
from flask import Flask
from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
from dotenv import load_dotenv

load_dotenv()

# Initialize Flask extensions
mongo = PyMongo()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


def create_app():
    """
    Application Factory: Creates and configures the Flask app.
    """
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration from environment variables
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY'),
        MONGO_URI=os.environ.get('MONGO_URI')
    )
    
    # Initialize the extensions with our app instance
    mongo.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        return User(user_data) if user_data else None

    with app.app_context():
        from . import models
        
        from .main.routes import main as main_blueprint
        app.register_blueprint(main_blueprint)

        from .auth.routes import auth as auth_blueprint
        app.register_blueprint(auth_blueprint, url_prefix='/auth')

        from .trade.routes import trade as trade_blueprint
        app.register_blueprint(trade_blueprint)

        from .research.routes import research as research_blueprint
        app.register_blueprint(research_blueprint)

    return app