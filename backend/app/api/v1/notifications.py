from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import Notification
from app.utils.response import success_response, paginated_response

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/v1/notifications')


@notifications_bp.route('', methods=['GET'])
@jwt_required()
def get_notifications():
    user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Notification.query.filter_by(user_id=user_id)
    total = query.count()
    notifs = query.order_by(Notification.created_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    unread_count = Notification.query.filter_by(
        user_id=user_id, is_read=False
    ).count()

    return success_response(data={
        'notifications': [n.to_dict() for n in notifs],
        'unread_count': unread_count,
        'pagination': {
            'total': total, 'page': page, 'per_page': per_page
        }
    })


@notifications_bp.route('/read-all', methods=['POST'])
@jwt_required()
def mark_all_read():
    user_id = int(get_jwt_identity())
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    return success_response(message='All notifications marked as read')


@notifications_bp.route('/<int:notif_id>/read', methods=['POST'])
@jwt_required()
def mark_read(notif_id):
    user_id = int(get_jwt_identity())
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != user_id:
        from app.utils.response import error_response
        return error_response('Forbidden', 403)
    notif.is_read = True
    db.session.commit()
    return success_response(message='Notification marked as read')


@notifications_bp.route('/<int:notif_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notif_id):
    user_id = int(get_jwt_identity())
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != user_id:
        from app.utils.response import error_response
        return error_response('Forbidden', 403)
    db.session.delete(notif)
    db.session.commit()
    return success_response(message='Notification deleted')


@notifications_bp.route('/bulk-delete', methods=['POST'])
@jwt_required()
def bulk_delete_notifications():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    ids = data.get('ids', [])
    if not ids:
        from app.utils.response import error_response
        return error_response('ids required', 400)
    Notification.query.filter(
        Notification.id.in_(ids),
        Notification.user_id == user_id
    ).delete(synchronize_session=False)
    db.session.commit()
    return success_response(message=f'{len(ids)} notifications deleted')
