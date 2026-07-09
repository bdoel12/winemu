from flask import jsonify


def success_response(data=None, message='Success', status_code=200, **kwargs):
    response = {
        'status': 'success',
        'message': message,
    }
    if data is not None:
        response['data'] = data
    response.update(kwargs)
    return jsonify(response), status_code


def error_response(message='Error', status_code=400, errors=None):
    response = {
        'status': 'error',
        'message': message,
    }
    if errors:
        response['errors'] = errors
    return jsonify(response), status_code


def paginated_response(items, total, page, per_page, message='Success', extra=None):
    payload = {
        'items': items,
        'pagination': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page,
            'has_next': page * per_page < total,
            'has_prev': page > 1,
        }
    }
    if extra:
        payload.update(extra)
    return jsonify({
        'status': 'success',
        'message': message,
        'data': payload
    }), 200
