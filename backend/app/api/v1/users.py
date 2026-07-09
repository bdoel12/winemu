from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models import User, Report, Bookmark, UserRating
from app.utils.response import success_response, error_response, paginated_response
from app.utils.upload import save_file, allowed_file

users_bp = Blueprint('users', __name__, url_prefix='/api/v1/users')


@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return error_response('User not found', 404)
    return success_response(data={'user': user.to_dict(include_private=True)})


@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return error_response('User not found', 404)

    data = request.get_json()
    updatable = ['full_name', 'bio', 'phone', 'location', 'latitude', 'longitude']
    for field in updatable:
        if field in data:
            setattr(user, field, data[field])

    db.session.commit()
    return success_response(data={'user': user.to_dict(include_private=True)},
                            message='Profile updated')


@users_bp.route('/profile/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return error_response('User not found', 404)

    if 'avatar' not in request.files:
        return error_response('No file provided', 400)

    file = request.files['avatar']
    if not allowed_file(file.filename, 'image'):
        return error_response('Invalid file type', 400)

    url, _ = save_file(file, subfolder='avatars')
    if not url:
        return error_response('Upload failed', 500)

    user.avatar_url = url
    db.session.commit()

    return success_response(data={'avatar_url': url}, message='Avatar updated')


@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return success_response(data={'user': user.to_dict()})


@users_bp.route('/<int:user_id>/reports', methods=['GET'])
def get_user_reports(user_id):
    user = User.query.get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    report_type = request.args.get('type')

    query = Report.query.filter_by(user_id=user_id, is_active=True)
    if report_type:
        query = query.filter_by(type=report_type)

    total = query.count()
    reports = query.order_by(Report.created_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    return paginated_response(
        items=[r.to_dict() for r in reports],
        total=total, page=page, per_page=per_page
    )


@users_bp.route('/bookmarks', methods=['GET'])
@jwt_required()
def get_bookmarks():
    user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    query = Bookmark.query.filter_by(user_id=user_id)
    total = query.count()
    bookmarks = query.order_by(Bookmark.created_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    return paginated_response(
        items=[b.to_dict() for b in bookmarks],
        total=total, page=page, per_page=per_page
    )


@users_bp.route('/bookmarks/<int:report_id>', methods=['POST', 'DELETE'])
@jwt_required()
def toggle_bookmark(report_id):
    user_id = int(get_jwt_identity())
    existing = Bookmark.query.filter_by(user_id=user_id, report_id=report_id).first()

    if request.method == 'POST':
        if existing:
            return success_response(message='Already bookmarked')
        bookmark = Bookmark(user_id=user_id, report_id=report_id)
        db.session.add(bookmark)
        db.session.commit()
        return success_response(message='Bookmarked', status_code=201)
    else:
        if existing:
            db.session.delete(existing)
            db.session.commit()
        return success_response(message='Bookmark removed')


def _recalculate_user_rating(user_id):
    """Recompute and persist the average rating for a user."""
    ratings = UserRating.query.filter_by(rated_user_id=user_id).all()
    user = User.query.get(user_id)
    if user:
        user.rating = round(sum(r.score for r in ratings) / len(ratings), 2) if ratings else 0.0
        db.session.commit()


@users_bp.route('/<int:user_id>/ratings', methods=['GET'])
def get_user_ratings(user_id):
    User.query.get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    query = UserRating.query.filter_by(rated_user_id=user_id)
    total = query.count()
    ratings = query.order_by(UserRating.created_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    breakdown = {str(i): UserRating.query.filter_by(rated_user_id=user_id, score=i).count() for i in range(1, 6)}

    return paginated_response(
        items=[r.to_dict() for r in ratings],
        total=total, page=page, per_page=per_page,
        extra={'breakdown': breakdown}
    )


@users_bp.route('/<int:user_id>/ratings', methods=['POST'])
@jwt_required()
def submit_rating(user_id):
    rater_id = int(get_jwt_identity())

    if rater_id == user_id:
        return error_response('Tidak dapat memberi rating untuk diri sendiri', 400)

    User.query.get_or_404(user_id)
    data = request.get_json() or {}
    score = data.get('score')
    report_id = data.get('report_id')
    comment = (data.get('comment') or '').strip()

    if not isinstance(score, int) or score < 1 or score > 5:
        return error_response('score wajib diisi (1-5)', 400)

    existing = UserRating.query.filter_by(
        rater_id=rater_id, rated_user_id=user_id, report_id=report_id
    ).first()

    if existing:
        existing.score = score
        existing.comment = comment
        rating = existing
        message = 'Rating diperbarui'
    else:
        rating = UserRating(
            rater_id=rater_id, rated_user_id=user_id,
            report_id=report_id, score=score, comment=comment
        )
        db.session.add(rating)
        message = 'Rating berhasil dikirim'

    db.session.commit()
    _recalculate_user_rating(user_id)

    return success_response(data={'rating': rating.to_dict()}, message=message, status_code=201)


def _haversine_km(lat1, lng1, lat2, lng2):
    """Jarak antara dua koordinat dalam kilometer (formula Haversine)."""
    import math
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2)
    return r * 2 * math.asin(math.sqrt(a))


@users_bp.route('/nearby', methods=['GET'])
@jwt_required()
def nearby_users():
    """
    Cari pengguna lain di sekitar lokasi yang diberikan (lat/lng query param,
    biasanya dari geolocation browser saat ini). Sumber lokasi tiap kandidat
    diambil dari dua tempat, mana yang tersedia:
      1. Lokasi yang diisi di profil pengguna (User.latitude/longitude)
      2. Lokasi laporan terbaru yang mereka buat (Report.latitude/longitude)
    Sehingga pengguna yang belum mengisi lokasi profil tetap bisa muncul
    selama mereka pernah membuat laporan dengan lokasi.
    """
    user_id = int(get_jwt_identity())
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius_km = request.args.get('radius', 15, type=float)
    limit = request.args.get('limit', 10, type=int)

    if lat is None or lng is None:
        return error_response('Parameter lat dan lng wajib diisi', 400)

    candidates = {}  # user_id -> {'user': User, 'lat':.., 'lng':.., 'distance_km':..}

    # Sumber 1: lokasi profil
    profile_users = User.query.filter(
        User.id != user_id,
        User.latitude.isnot(None),
        User.longitude.isnot(None),
        User.is_active == True,
    ).all()
    for u in profile_users:
        dist = _haversine_km(lat, lng, u.latitude, u.longitude)
        if dist <= radius_km:
            candidates[u.id] = {'user': u, 'distance_km': round(dist, 1)}

    # Sumber 2: lokasi laporan terbaru (ambil laporan aktif/proses terbaru per user)
    recent_reports = Report.query.filter(
        Report.latitude.isnot(None),
        Report.longitude.isnot(None),
        Report.is_active == True,
        Report.status.in_(['aktif', 'proses']),
        Report.user_id != user_id,
    ).order_by(Report.created_at.desc()).limit(200).all()

    for r in recent_reports:
        if r.user_id in candidates:
            continue  # Sudah ada dari lokasi profil, profil lebih diutamakan
        dist = _haversine_km(lat, lng, r.latitude, r.longitude)
        if dist <= radius_km:
            u = User.query.get(r.user_id)
            if u and u.is_active:
                candidates[u.id] = {'user': u, 'distance_km': round(dist, 1)}

    sorted_candidates = sorted(candidates.values(), key=lambda c: c['distance_km'])[:limit]

    return success_response(data={
        'users': [
            {**c['user'].to_dict(), 'distance_km': c['distance_km']}
            for c in sorted_candidates
        ]
    })
