import os
from flask import Flask, send_from_directory, jsonify
from flask_jwt_extended import JWTManager

from app.config import config_map
from app.extensions import db, migrate, jwt, socketio, cors, ma


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__, static_folder='static', template_folder='templates')
    
    # Load config
    cfg = config_map.get(config_name, config_map['default'])
    app.config.from_object(cfg)

    # Ensure upload folder exists
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'static/uploads'), exist_ok=True)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)
    cors.init_app(app, resources={
        r"/api/*": {"origins": "*"},
        r"/socket.io/*": {"origins": "*"}
    })
    socketio.init_app(app,
                      cors_allowed_origins="*",
                      async_mode='eventlet',
                      logger=False,
                      engineio_logger=False)

    # Register all models (for migrations)
    with app.app_context():
        from app.models import (
            User, Report, ReportMedia, ReportLike,
            Category, Comment, Bookmark,
            Notification, Conversation, Message, ActivityLog
        )

    # Register blueprints
    from app.api.v1 import all_blueprints
    for bp in all_blueprints:
        app.register_blueprint(bp)

    # Register SocketIO events
    from app.sockets import register_socket_events
    register_socket_events(socketio)

    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'status': 'error', 'message': 'Token expired'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'status': 'error', 'message': 'Invalid token'}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'status': 'error', 'message': 'Authorization required'}), 401

    # Health check
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'app': 'Winemu'})

    # Serve frontend static files
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        # app/__init__.py -> app -> backend -> winemu -> winemu/frontend
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_root = os.path.dirname(backend_dir)
        frontend_dir = os.path.join(project_root, 'frontend')

        full_path = os.path.join(frontend_dir, path) if path else frontend_dir

        # Kasus folder (mis. /desktop/, /admin/, atau root '') - cari index.html
        # di dalamnya, persis seperti web server pada umumnya. send_from_directory
        # tidak bisa melayani direktori secara langsung, jadi ini harus ditangani
        # secara eksplisit sebelum dicoba sebagai file.
        if os.path.isdir(full_path):
            index_rel_path = os.path.join(path, 'index.html') if path else 'index.html'
            if os.path.exists(os.path.join(frontend_dir, index_rel_path)):
                return send_from_directory(frontend_dir, index_rel_path)
            # Folder ada tapi tidak punya index.html - lanjut ke fallback di bawah.
        elif path and os.path.isfile(full_path):
            return send_from_directory(frontend_dir, path)

        # Fallback: path tidak dikenali sama sekali (mis. route client-side) -
        # serve index.html root seperti semula.
        return send_from_directory(frontend_dir, 'index.html')

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'status': 'error', 'message': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

    return app
