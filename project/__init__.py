from flask import Flask 
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_mail import Mail
import os 
from dotenv import load_dotenv

load_dotenv()

if os.getenv('FLASK_DEBUG') == '1':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()

def create_app():
  app = Flask(__name__)

  supabase_db_url = os.getenv('SUPABASE_DB_URL')
  
  if not supabase_db_url:
    raise ValueError("SUPABASE_DB_URL environment variable is not set. Please check your .env file.")

  if supabase_db_url.startswith("postgres://"):
      supabase_db_url = supabase_db_url.replace("postgres://", "postgresql://", 1)

  app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'key-goes-here')
  app.config['SQLALCHEMY_DATABASE_URI'] = supabase_db_url
  app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
  app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
  }
  app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
  app.config['MAIL_PORT'] = 587
  app.config['MAIL_USE_TLS'] = True
  app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'username@gmail.com')
  app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'password')

  db.init_app(app)

  login_manager = LoginManager()
  login_manager.login_view = 'auth.login'
  login_manager.init_app(app)

  jwt.init_app(app)
  mail.init_app(app)

  from .models import User, OAuth

  @login_manager.user_loader
  def load_user(user_id):
    return User.query.get(int(user_id))

  from .auth import auth as auth_blueprint
  app.register_blueprint(auth_blueprint)

  from .social_login import google_blueprint
  app.register_blueprint(google_blueprint, url_prefix = "/login")

  from .main import main as main_blueprint
  app.register_blueprint(main_blueprint)

  return app