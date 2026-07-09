from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone

from app.extensions import db, socketio
from app.models import Conversation, Message, User, Report
from app.utils.response import success_response, error_response, paginated_response

chat_bp = Blueprint('chat', __name__, url_prefix='/api/v1/chat')


@chat_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    from sqlalchemy import or_
    query = Conversation.query.filter(
        or_(
            Conversation.user1_id == user_id,
            Conversation.user2_id == user_id
        )
    )
    total = query.count()
    convs = query.order_by(Conversation.last_message_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    return paginated_response(
        items=[c.to_dict(user_id) for c in convs],
        total=total, page=page, per_page=per_page
    )


@chat_bp.route('/conversations', methods=['POST'])
@jwt_required()
def create_conversation():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    try:
        other_user_id = int(data.get('user_id'))
    except (TypeError, ValueError):
        return error_response('user_id harus berupa angka', 400)
    
    report_id_raw = data.get('report_id')
    try:
        report_id = int(report_id_raw) if report_id_raw is not None else None
    except (TypeError, ValueError):
        report_id = None

    if not other_user_id:
        return error_response('user_id required', 400)
    if other_user_id == user_id:
        return error_response('Tidak bisa chat dengan diri sendiri', 400)

    other_user = User.query.get(other_user_id)
    if not other_user:
        return error_response(f'Pengguna dengan ID {other_user_id} tidak ditemukan', 404)

    # Check if conversation already exists
    from sqlalchemy import or_, and_
    existing = Conversation.query.filter(
        or_(
            and_(Conversation.user1_id == user_id, Conversation.user2_id == other_user_id),
            and_(Conversation.user1_id == other_user_id, Conversation.user2_id == user_id)
        )
    )
    if report_id:
        existing = existing.filter_by(report_id=report_id)

    existing = existing.first()
    if existing:
        return success_response(data={'conversation': existing.to_dict(user_id)})

    conv = Conversation(
        user1_id=user_id,
        user2_id=other_user_id,
        report_id=report_id,
        last_message_at=datetime.now(timezone.utc)
    )
    db.session.add(conv)
    db.session.commit()

    return success_response(
        data={'conversation': conv.to_dict(user_id)},
        status_code=201
    )


@chat_bp.route('/conversations/<int:conv_id>', methods=['DELETE'])
@jwt_required()
def delete_conversation(conv_id):
    user_id = int(get_jwt_identity())
    conv = Conversation.query.get_or_404(conv_id)

    if conv.user1_id != user_id and conv.user2_id != user_id:
        return error_response('Forbidden', 403)

    db.session.delete(conv)
    db.session.commit()

    return success_response(data={'message': 'Conversation deleted'})


@chat_bp.route('/conversations/<int:conv_id>/messages', methods=['DELETE'])
@jwt_required()
def clear_messages(conv_id):
    user_id = int(get_jwt_identity())
    conv = Conversation.query.get_or_404(conv_id)

    if conv.user1_id != user_id and conv.user2_id != user_id:
        return error_response('Forbidden', 403)

    Message.query.filter_by(conversation_id=conv_id).delete()
    conv.last_message_at = None
    db.session.commit()

    return success_response(data={'message': 'All messages cleared'})


@chat_bp.route('/conversations/<int:conv_id>/messages', methods=['GET'])
@jwt_required()
def get_messages(conv_id):
    user_id = int(get_jwt_identity())
    conv = Conversation.query.get_or_404(conv_id)

    if conv.user1_id != user_id and conv.user2_id != user_id:
        return error_response('Forbidden', 403)

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    query = Message.query.filter_by(conversation_id=conv_id)
    total = query.count()
    messages = query.order_by(Message.created_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    # Mark as read
    Message.query.filter_by(
        conversation_id=conv_id, is_read=False
    ).filter(Message.sender_id != user_id).update({'is_read': True})
    db.session.commit()

    return paginated_response(
        items=[m.to_dict() for m in reversed(messages)],
        total=total, page=page, per_page=per_page
    )


@chat_bp.route('/conversations/<int:conv_id>/messages', methods=['POST'])
@jwt_required()
def send_message(conv_id):
    user_id = int(get_jwt_identity())
    conv = Conversation.query.get_or_404(conv_id)

    if conv.user1_id != user_id and conv.user2_id != user_id:
        return error_response('Forbidden', 403)

    data = request.get_json()
    content = data.get('content', '').strip()
    if not content:
        return error_response('Content required', 400)

    reply_to_id_raw = data.get('reply_to_id')
    try:
        reply_to_id = int(reply_to_id_raw) if reply_to_id_raw is not None else None
    except (TypeError, ValueError):
        reply_to_id = None
    reply_to_content = data.get('reply_to_content', '')
    reply_to_sender = data.get('reply_to_sender', '')
    # Validate reply_to_id if provided
    if reply_to_id:
        ref = Message.query.filter_by(id=reply_to_id, conversation_id=conv_id).first()
        if not ref:
            reply_to_id = None
            reply_to_content = None
            reply_to_sender = None
        else:
            if not reply_to_content:
                reply_to_content = ref.content[:200]
            if not reply_to_sender and ref.sender:
                reply_to_sender = ref.sender.full_name

    msg = Message(
        conversation_id=conv_id,
        sender_id=user_id,
        content=content,
        type=data.get('type', 'text'),
        reply_to_id=reply_to_id,
        reply_to_content=reply_to_content,
        reply_to_sender=reply_to_sender,
    )
    db.session.add(msg)
    conv.last_message_at = datetime.now(timezone.utc)
    db.session.commit()

    # Emit message to conversation room (for open chat windows)
    socketio.emit('new_message', msg.to_dict(), room=f'conv_{conv_id}')

    # Emit notification to recipient's personal room (for badge/toast when chat is closed)
    recipient_id = conv.user2_id if conv.user1_id == user_id else conv.user1_id
    sender = User.query.get(user_id)
    socketio.emit('new_notification', {
        'type': 'chat',
        'title': f'Pesan dari {sender.full_name if sender else "Seseorang"}',
        'message': content[:80] + ('...' if len(content) > 80 else ''),
        'actor': sender.to_dict() if sender else None,
    }, room=f'user_{recipient_id}')

    # Persist notification to DB
    from app.models import Notification
    notif = Notification(
        user_id=recipient_id,
        actor_id=user_id,
        type='chat',
        title=f'Pesan dari {sender.full_name if sender else "Seseorang"}',
        message=content[:100],
        data={'conversation_id': conv_id}
    )
    db.session.add(notif)
    db.session.commit()

    return success_response(
        data={'message': msg.to_dict()},
        status_code=201
    )


@chat_bp.route('/messages/<int:msg_id>', methods=['DELETE'])
@jwt_required()
def delete_message(msg_id):
    user_id = int(get_jwt_identity())
    msg = Message.query.get_or_404(msg_id)
    conv = Conversation.query.get_or_404(msg.conversation_id)

    # Only sender or conversation participant can delete
    if msg.sender_id != user_id and conv.user1_id != user_id and conv.user2_id != user_id:
        return error_response('Forbidden', 403)

    conv_id = msg.conversation_id
    db.session.delete(msg)

    # Update last_message_at to latest remaining message
    latest = Message.query.filter_by(conversation_id=conv_id).order_by(Message.created_at.desc()).first()
    conv.last_message_at = latest.created_at if latest else None
    db.session.commit()

    socketio.emit('message_deleted', {'message_id': msg_id}, room=f'conv_{conv_id}')
    return success_response(data={'message_id': msg_id})


@chat_bp.route('/messages/<int:msg_id>/pin', methods=['POST'])
@jwt_required()
def pin_message(msg_id):
    user_id = int(get_jwt_identity())
    msg = Message.query.get_or_404(msg_id)
    conv = Conversation.query.get_or_404(msg.conversation_id)

    if conv.user1_id != user_id and conv.user2_id != user_id:
        return error_response('Forbidden', 403)

    msg.is_pinned = not msg.is_pinned
    db.session.commit()

    socketio.emit('message_pinned', {'message_id': msg_id, 'is_pinned': msg.is_pinned}, room=f'conv_{msg.conversation_id}')
    return success_response(data={'message_id': msg_id, 'is_pinned': msg.is_pinned})


@chat_bp.route('/conversations/<int:conv_id>/pinned', methods=['GET'])
@jwt_required()
def get_pinned_messages(conv_id):
    user_id = int(get_jwt_identity())
    conv = Conversation.query.get_or_404(conv_id)

    if conv.user1_id != user_id and conv.user2_id != user_id:
        return error_response('Forbidden', 403)

    pinned = Message.query.filter_by(conversation_id=conv_id, is_pinned=True).order_by(Message.created_at.desc()).all()
    return success_response(data={'pinned': [m.to_dict() for m in pinned]})
