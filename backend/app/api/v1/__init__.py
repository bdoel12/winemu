from flask import Blueprint
from .auth import auth_bp
from .users import users_bp
from .reports import reports_bp
from .categories import categories_bp
from .chat import chat_bp
from .notifications import notifications_bp
from .admin import admin_bp
from .claims import claims_bp

api_v1_bp = Blueprint('api_v1', __name__)

all_blueprints = [
    auth_bp, users_bp, reports_bp,
    categories_bp, chat_bp, notifications_bp,
    admin_bp, claims_bp,
]
