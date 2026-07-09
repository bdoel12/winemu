from flask_socketio import join_room, leave_room, emit
from flask_jwt_extended import decode_token


def register_socket_events(socketio):

    @socketio.on('connect')
    def handle_connect(auth):
        pass

    @socketio.on('join_conversation')
    def handle_join(data):
        room = f"conv_{data.get('conversation_id')}"
        join_room(room)
        emit('joined', {'room': room})

    @socketio.on('leave_conversation')
    def handle_leave(data):
        room = f"conv_{data.get('conversation_id')}"
        leave_room(room)

    @socketio.on('join_user_room')
    def handle_join_user(data):
        user_id = data.get('user_id')
        if user_id:
            join_room(f'user_{user_id}')

    @socketio.on('typing')
    def handle_typing(data):
        room = f"conv_{data.get('conversation_id')}"
        emit('user_typing', {
            'user_id': data.get('user_id'),
            'conversation_id': data.get('conversation_id')
        }, room=room, include_self=False)

    @socketio.on('disconnect')
    def handle_disconnect():
        pass
