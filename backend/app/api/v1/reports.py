from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from flask_jwt_extended.exceptions import NoAuthorizationError
from sqlalchemy import or_, and_

from app.extensions import db, socketio
from app.models import Report, ReportMedia, ReportLike, Comment, Notification, User
from app.utils.response import success_response, error_response, paginated_response
from app.utils.upload import save_file, allowed_file

reports_bp = Blueprint('reports', __name__, url_prefix='/api/v1/reports')


def get_optional_user_id():
    try:
        verify_jwt_in_request(optional=True)
        from flask_jwt_extended import get_jwt_identity
        uid = get_jwt_identity()
        return int(uid) if uid else None
    except Exception:
        return None


@reports_bp.route('', methods=['GET'])
def get_reports():
    current_user_id = get_optional_user_id()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    report_type = request.args.get('type')
    category_id = request.args.get('category_id', type=int)
    status = request.args.get('status')
    search = request.args.get('q')
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)

    query = Report.query.filter_by(is_active=True)

    if report_type:
        query = query.filter_by(type=report_type)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if status:
        query = query.filter_by(status=status)
    else:
        # Secara default, feed publik hanya menampilkan laporan yang masih
        # aktif/dalam proses. Barang yang sudah berhasil dikembalikan (selesai)
        # atau ditutup tidak perlu lagi muncul di feed beranda.
        query = query.filter(Report.status.in_(['aktif', 'proses']))
    if search:
        query = query.filter(
            or_(
                Report.title.ilike(f'%{search}%'),
                Report.description.ilike(f'%{search}%'),
                Report.location_name.ilike(f'%{search}%')
            )
        )

    total = query.count()
    reports = query.order_by(Report.created_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    return paginated_response(
        items=[r.to_dict(current_user_id) for r in reports],
        total=total, page=page, per_page=per_page
    )


@reports_bp.route('/<int:report_id>', methods=['GET'])
def get_report(report_id):
    current_user_id = get_optional_user_id()
    report = Report.query.get_or_404(report_id)

    report.view_count = (report.view_count or 0) + 1
    db.session.commit()

    return success_response(data={'report': report.to_dict(current_user_id)})


@reports_bp.route('', methods=['POST'])
@jwt_required()
def create_report():
    user_id = int(get_jwt_identity())

    report_type = request.form.get('type')
    title = request.form.get('title', '').strip()

    if not report_type or report_type not in ('hilang', 'ditemukan'):
        return error_response('type must be hilang or ditemukan', 400)
    if not title:
        return error_response('title is required', 400)

    report = Report(
        user_id=user_id,
        type=report_type,
        title=title,
        description=request.form.get('description'),
        category_id=request.form.get('category_id', type=int),
        verification_question=request.form.get('verification_question'),
        verification_answer=request.form.get('verification_answer'),
        location_name=request.form.get('location_name'),
        latitude=request.form.get('latitude', type=float),
        longitude=request.form.get('longitude', type=float),
        reward=request.form.get('reward'),
        contact_info=request.form.get('contact_info'),
    )
    db.session.add(report)
    db.session.flush()

    # Handle media uploads (max 10 images + max 3 videos = max 13 files total)
    files = request.files.getlist('media')
    image_count = 0
    video_count = 0
    order = 0
    for file in files:
        if not file or not file.filename:
            continue
        is_image = allowed_file(file.filename, 'image')
        is_video = allowed_file(file.filename, 'video')
        if not is_image and not is_video:
            continue
        if is_image and image_count >= 10:
            continue  # skip beyond image limit
        if is_video and video_count >= 3:
            continue  # skip beyond video limit
        url, file_type = save_file(file, subfolder='reports')
        if url:
            media = ReportMedia(
                report_id=report.id,
                url=url,
                type=file_type,
                filename=file.filename,
                order=order
            )
            db.session.add(media)
            order += 1
            if file_type == 'image':
                image_count += 1
            else:
                video_count += 1

    # Update user stats
    user = User.query.get(user_id)
    if user:
        user.total_reports = (user.total_reports or 0) + 1

    db.session.commit()

    return success_response(
        data={'report': report.to_dict(user_id)},
        message='Report created successfully',
        status_code=201
    )


@reports_bp.route('/<int:report_id>', methods=['PUT'])
@jwt_required()
def update_report(report_id):
    user_id = int(get_jwt_identity())
    report = Report.query.get_or_404(report_id)

    if report.user_id != user_id:
        user = User.query.get(user_id)
        if not user or user.role not in ('admin', 'moderator'):
            return error_response('Forbidden', 403)

    data = request.get_json() or {}
    updatable = ['title', 'description', 'category_id', 'location_name',
                 'latitude', 'longitude', 'reward', 'contact_info', 'status']
    for field in updatable:
        if field in data:
            setattr(report, field, data[field])

    db.session.commit()
    return success_response(data={'report': report.to_dict(user_id)},
                            message='Report updated')


@reports_bp.route('/<int:report_id>', methods=['DELETE'])
@jwt_required()
def delete_report(report_id):
    user_id = int(get_jwt_identity())
    report = Report.query.get_or_404(report_id)

    if report.user_id != user_id:
        user = User.query.get(user_id)
        if not user or user.role not in ('admin', 'moderator'):
            return error_response('Forbidden', 403)

    report.is_active = False
    db.session.commit()
    return success_response(message='Report deleted')


@reports_bp.route('/<int:report_id>/like', methods=['POST'])
@jwt_required()
def toggle_like(report_id):
    user_id = int(get_jwt_identity())
    report = Report.query.get_or_404(report_id)

    existing = ReportLike.query.filter_by(report_id=report_id, user_id=user_id).first()
    if existing:
        db.session.delete(existing)
        report.like_count = max(0, (report.like_count or 0) - 1)
        liked = False
    else:
        like = ReportLike(report_id=report_id, user_id=user_id)
        db.session.add(like)
        report.like_count = (report.like_count or 0) + 1
        liked = True

        # Notify report author
        if report.user_id != user_id:
            notif = Notification(
                user_id=report.user_id,
                actor_id=user_id,
                type='like',
                title='Seseorang menyukai laporanmu',
                message=f'Laporan "{report.title}" disukai',
                data={'report_id': report_id}
            )
            db.session.add(notif)
            actor = User.query.get(user_id)
            socketio.emit('new_notification', {
                'type': 'like',
                'title': 'Seseorang menyukai laporanmu',
                'message': f'Laporan "{report.title}" disukai',
                'actor': actor.to_dict() if actor else None,
            }, room=f'user_{report.user_id}')

    db.session.commit()
    return success_response(data={'liked': liked, 'like_count': report.like_count})


@reports_bp.route('/<int:report_id>/comments', methods=['GET'])
def get_comments(report_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Comment.query.filter_by(report_id=report_id, parent_id=None, is_active=True)
    total = query.count()
    comments = query.order_by(Comment.created_at.asc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    return paginated_response(
        items=[c.to_dict() for c in comments],
        total=total, page=page, per_page=per_page
    )


@reports_bp.route('/<int:report_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(report_id):
    user_id = int(get_jwt_identity())
    report = Report.query.get_or_404(report_id)
    data = request.get_json()

    content = data.get('content', '').strip()
    if not content:
        return error_response('Comment content required', 400)

    comment = Comment(
        report_id=report_id,
        user_id=user_id,
        content=content,
        parent_id=data.get('parent_id')
    )
    db.session.add(comment)
    report.comment_count = (report.comment_count or 0) + 1

    # Notify
    if report.user_id != user_id:
        notif = Notification(
            user_id=report.user_id,
            actor_id=user_id,
            type='comment',
            title='Komentar baru',
            message=f'Ada komentar baru pada laporan "{report.title}"',
            data={'report_id': report_id, 'comment_id': None}
        )
        db.session.add(notif)
        actor = User.query.get(user_id)
        socketio.emit('new_notification', {
            'type': 'comment',
            'title': 'Komentar baru',
            'message': f'Ada komentar baru pada laporan "{report.title}"',
            'actor': actor.to_dict() if actor else None,
        }, room=f'user_{report.user_id}')

    db.session.commit()
    
    return success_response(
        data={'comment': comment.to_dict()},
        message='Comment added',
        status_code=201
    )


@reports_bp.route('/<int:report_id>/media', methods=['POST'])
@jwt_required()
def upload_media(report_id):
    user_id = int(get_jwt_identity())
    report = Report.query.get_or_404(report_id)

    if report.user_id != user_id:
        return error_response('Forbidden', 403)

    files = request.files.getlist('media')
    if not files:
        return error_response('No files provided', 400)

    uploaded = []
    for file in files:
        if file and file.filename:
            url, file_type = save_file(file, subfolder='reports')
            if url:
                media = ReportMedia(
                    report_id=report_id,
                    url=url, type=file_type, filename=file.filename
                )
                db.session.add(media)
                uploaded.append({'url': url, 'type': file_type})

    db.session.commit()
    return success_response(data={'media': uploaded}, message='Media uploaded',
                            status_code=201)

@reports_bp.route('/<int:report_id>/share', methods=['POST'])
def increment_share(report_id):
    report = Report.query.get_or_404(report_id)
    report.share_count = (report.share_count or 0) + 1
    db.session.commit()
    return success_response(data={'share_count': report.share_count})

@reports_bp.route('/<int:report_id>/flag', methods=['POST'])
@jwt_required()
def flag_report(report_id):
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    category = data.get('category', 'Tidak diketahui')
    from app.models import Notification
    from app.models.user import User
    from app.extensions import socketio
    admins = User.query.filter_by(role='admin').all()
    for admin in admins:
        notif = Notification(user_id=admin.id, actor_id=user_id, type='flag',
            title='Laporan pelanggaran baru',
            message=f'Postingan #{report_id} dilaporkan: {category}',
            data={'report_id': report_id, 'category': category})
        db.session.add(notif)
        socketio.emit('new_notification', {'type':'flag','title':'Laporan pelanggaran','message':f'{category}'}, room=f'user_{admin.id}')
    db.session.commit()
    return success_response(data={'flagged': True})
