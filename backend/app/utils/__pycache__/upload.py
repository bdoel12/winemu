import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app


ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}


def allowed_file(filename, file_type='image'):
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    if file_type == 'image':
        return ext in ALLOWED_IMAGE_EXTENSIONS
    elif file_type == 'video':
        return ext in ALLOWED_VIDEO_EXTENSIONS
    return ext in ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS


def save_file(file, subfolder='reports'):
    """Save uploaded file to local storage, return URL path."""
    if not file or not file.filename:
        return None, None

    ext = file.filename.rsplit('.', 1)[-1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    
    filepath = os.path.join(upload_dir, unique_name)
    file.save(filepath)
    
    url = f"/static/uploads/{subfolder}/{unique_name}"
    file_type = 'video' if ext in ALLOWED_VIDEO_EXTENSIONS else 'image'
    
    return url, file_type


def delete_file(url):
    """Delete a file from local storage by its URL."""
    if not url:
        return
    # Convert URL to filesystem path
    relative = url.lstrip('/')
    full_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        relative
    )
    if os.path.exists(full_path):
        os.remove(full_path)
