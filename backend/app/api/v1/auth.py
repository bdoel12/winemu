from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime, timezone
import secrets

from app.extensions import db
from app.models import User, ActivityLog
from app.utils.response import success_response, error_response

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return error_response('No data provided', 400)

    required = ['username', 'email', 'password']
    for field in required:
        if not data.get(field):
            return error_response(f'{field} is required', 400)

    if len(data['password']) < 6:
        return error_response('Password must be at least 6 characters', 400)

    if User.query.filter_by(email=data['email'].lower()).first():
        return error_response('Email already registered', 409)
    if User.query.filter_by(username=data['username'].lower()).first():
        return error_response('Username already taken', 409)

    user = User(
        username=data['username'].lower().strip(),
        email=data['email'].lower().strip(),
        full_name=data.get('full_name', ''),
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.flush()

    log = ActivityLog(user_id=user.id, action='register',
                      ip_address=request.remote_addr)
    db.session.add(log)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return success_response(
        data={
            'user': user.to_dict(include_private=True),
            'access_token': access_token,
            'refresh_token': refresh_token,
        },
        message='Registration successful',
        status_code=201
    )


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return error_response('No data provided', 400)

    email_or_username = data.get('email') or data.get('username')
    password = data.get('password')

    if not email_or_username or not password:
        return error_response('Email/username and password required', 400)

    user = User.query.filter(
        (User.email == email_or_username.lower()) |
        (User.username == email_or_username.lower())
    ).first()

    if not user or not user.check_password(password):
        return error_response('Invalid credentials', 401)

    if not user.is_active:
        return error_response('Account is disabled', 403)

    user.last_login = datetime.now(timezone.utc)
    log = ActivityLog(user_id=user.id, action='login',
                      ip_address=request.remote_addr)
    db.session.add(log)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return success_response(data={
        'user': user.to_dict(include_private=True),
        'access_token': access_token,
        'refresh_token': refresh_token,
    }, message='Login successful')


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user or not user.is_active:
        return error_response('User not found', 404)

    access_token = create_access_token(identity=str(user.id))
    return success_response(data={'access_token': access_token})


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return error_response('User not found', 404)
    return success_response(data={'user': user.to_dict(include_private=True)})


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    user_id = get_jwt_identity()
    log = ActivityLog(user_id=int(user_id), action='logout',
                      ip_address=request.remote_addr)
    db.session.add(log)
    db.session.commit()
    return success_response(message='Logged out successfully')


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email', '').lower()
    user = User.query.filter_by(email=email).first()
    
    # Always return success to prevent email enumeration
    if user:
        token = secrets.token_urlsafe(32)
        from datetime import timedelta
        user.reset_token = token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        db.session.commit()
        # In production: send email with reset link
    
    return success_response(message='If email exists, reset link has been sent')


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('password')

    if not token or not new_password:
        return error_response('Token and new password required', 400)
    if len(new_password) < 6:
        return error_response('Password must be at least 6 characters', 400)

    user = User.query.filter_by(reset_token=token).first()
    if not user:
        return error_response('Invalid or expired token', 400)
    if user.reset_token_expires < datetime.now(timezone.utc):
        return error_response('Token expired', 400)

    user.set_password(new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.session.commit()

    return success_response(message='Password reset successful')
