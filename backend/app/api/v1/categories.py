from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import Category, User
from app.utils.response import success_response, error_response

categories_bp = Blueprint('categories', __name__, url_prefix='/api/v1/categories')


@categories_bp.route('', methods=['GET'])
def get_categories():
    cats = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    return success_response(data={'categories': [c.to_dict() for c in cats]})


@categories_bp.route('', methods=['POST'])
@jwt_required()
def create_category():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return error_response('Admin only', 403)

    data = request.get_json()
    name = data.get('name', '').strip()
    if not name:
        return error_response('Name required', 400)

    slug = name.lower().replace(' ', '-')
    cat = Category(
        name=name, slug=slug,
        icon=data.get('icon', 'category'),
        description=data.get('description')
    )
    db.session.add(cat)
    db.session.commit()
    return success_response(data={'category': cat.to_dict()}, status_code=201)


@categories_bp.route('/<int:cat_id>', methods=['PUT', 'DELETE'])
@jwt_required()
def manage_category(cat_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return error_response('Admin only', 403)

    cat = Category.query.get_or_404(cat_id)

    if request.method == 'DELETE':
        cat.is_active = False
        db.session.commit()
        return success_response(message='Category deleted')

    data = request.get_json()
    for field in ['name', 'icon', 'description']:
        if field in data:
            setattr(cat, field, data[field])
    db.session.commit()
    return success_response(data={'category': cat.to_dict()})
