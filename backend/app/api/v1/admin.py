from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from datetime import datetime, timezone, timedelta

from app.extensions import db
from app.models import User, Report, Comment, ActivityLog, Claim
from app.utils.response import success_response, error_response, paginated_response

admin_bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')


def require_admin():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return None, error_response('Admin access required', 403)
    return user, None


@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    user, err = require_admin()
    if err:
        return err

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    total_users = User.query.count()
    inactive_users = User.query.filter_by(is_active=False).count()
    total_reports = Report.query.count()
    active_reports = Report.query.filter_by(status='aktif', is_active=True).count()
    solved_reports = Report.query.filter_by(status='selesai').count()
    new_users_week = User.query.filter(User.created_at >= week_ago).count()
    new_reports_week = Report.query.filter(Report.created_at >= week_ago).count()

    # Reports by type
    hilang_count = Report.query.filter_by(type='hilang', is_active=True).count()
    ditemukan_count = Report.query.filter_by(type='ditemukan', is_active=True).count()

    # Recent activity
    recent_reports = Report.query.filter_by(is_active=True).order_by(
        Report.created_at.desc()
    ).limit(5).all()

    return success_response(data={
        'stats': {
            'total_users': total_users,
            'inactive_users': inactive_users,
            'total_reports': total_reports,
            'active_reports': active_reports,
            'solved_reports': solved_reports,
            'new_users_week': new_users_week,
            'new_reports_week': new_reports_week,
            'hilang_count': hilang_count,
            'ditemukan_count': ditemukan_count,
        },
        'recent_reports': [r.to_dict() for r in recent_reports]
    })


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    user, err = require_admin()
    if err:
        return err

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('q')

    query = User.query
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.full_name.ilike(f'%{search}%'))
        )

    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    return paginated_response(
        items=[u.to_dict(include_private=True) for u in users],
        total=total, page=page, per_page=per_page
    )


@admin_bp.route('/users/<int:uid>', methods=['PUT'])
@jwt_required()
def update_user(uid):
    user, err = require_admin()
    if err:
        return err

    target = User.query.get_or_404(uid)
    data = request.get_json()

    for field in ['role', 'is_active', 'is_verified']:
        if field in data:
            setattr(target, field, data[field])

    db.session.commit()
    return success_response(data={'user': target.to_dict(include_private=True)})


@admin_bp.route('/reports', methods=['GET'])
@jwt_required()
def list_reports():
    user, err = require_admin()
    if err:
        return err

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    report_type = request.args.get('type')

    query = Report.query
    if status:
        query = query.filter_by(status=status)
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


@admin_bp.route('/reports/<int:rid>/verify', methods=['POST'])
@jwt_required()
def verify_report(rid):
    user, err = require_admin()
    if err:
        return err

    report = Report.query.get_or_404(rid)
    report.is_verified = True
    db.session.commit()
    return success_response(message='Report verified')


@admin_bp.route('/reports/<int:rid>', methods=['DELETE'])
@jwt_required()
def delete_report(rid):
    user, err = require_admin()
    if err:
        return err

    report = Report.query.get_or_404(rid)
    report.is_active = False
    db.session.commit()
    return success_response(message='Report removed')


@admin_bp.route('/conflicts', methods=['GET'])
@jwt_required()
def list_conflicts():
    """List claims that require admin attention (disputed or pending with multiple claimants)."""
    user, err = require_admin()
    if err:
        return err

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')  # disputed, pending, approved, rejected
    priority = request.args.get('priority')
    search = request.args.get('q')

    query = Claim.query
    if status:
        query = query.filter_by(status=status)
    else:
        query = query.filter(Claim.status.in_(['disputed', 'pending']))
    if priority:
        query = query.filter_by(priority=priority)
    if search:
        query = query.join(Report).filter(Report.title.ilike(f'%{search}%'))

    total = query.count()
    claims = query.order_by(Claim.created_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    return paginated_response(
        items=[c.to_dict() for c in claims],
        total=total, page=page, per_page=per_page
    )


@admin_bp.route('/conflicts/stats', methods=['GET'])
@jwt_required()
def conflict_stats():
    user, err = require_admin()
    if err:
        return err

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)

    active_disputes = Claim.query.filter(Claim.status.in_(['disputed', 'pending'])).count()
    urgent = Claim.query.filter(
        Claim.status.in_(['disputed', 'pending']),
        Claim.deadline.isnot(None),
        Claim.deadline <= now + timedelta(hours=24)
    ).count()
    resolved_today = Claim.query.filter(
        Claim.status.in_(['approved', 'rejected']),
        Claim.resolved_at >= today_start
    ).count()
    resolved_week = Claim.query.filter(
        Claim.status.in_(['approved', 'rejected']),
        Claim.resolved_at >= week_ago,
        Claim.resolved_at.isnot(None)
    ).all()

    avg_resolution_days = 0
    if resolved_week:
        deltas = [(c.resolved_at - c.created_at).total_seconds() / 86400 for c in resolved_week if c.resolved_at]
        if deltas:
            avg_resolution_days = round(sum(deltas) / len(deltas), 1)

    return success_response(data={
        'active_disputes': active_disputes,
        'urgent': urgent,
        'resolved_today': resolved_today,
        'avg_resolution_days': avg_resolution_days,
    })


@admin_bp.route('/conflicts/<int:claim_id>/approve', methods=['POST'])
@jwt_required()
def admin_approve_claim(claim_id):
    user, err = require_admin()
    if err:
        return err

    claim = Claim.query.get_or_404(claim_id)
    claim.status = 'approved'
    claim.resolved_by = user.id
    claim.resolved_at = datetime.now(timezone.utc)
    claim.handover_status = 'menunggu_metode'
    claim.report.status = 'proses'

    Claim.query.filter(
        Claim.report_id == claim.report_id,
        Claim.id != claim.id,
        Claim.status.in_(['pending', 'disputed'])
    ).update({'status': 'rejected', 'resolved_by': user.id,
              'resolved_at': datetime.now(timezone.utc)}, synchronize_session=False)

    db.session.commit()
    return success_response(data={'claim': claim.to_dict()}, message='Sengketa diselesaikan: klaim disetujui')


@admin_bp.route('/conflicts/<int:claim_id>/reject', methods=['POST'])
@jwt_required()
def admin_reject_claim(claim_id):
    user, err = require_admin()
    if err:
        return err

    claim = Claim.query.get_or_404(claim_id)
    claim.status = 'rejected'
    claim.resolved_by = user.id
    claim.resolved_at = datetime.now(timezone.utc)
    db.session.commit()
    return success_response(data={'claim': claim.to_dict()}, message='Sengketa diselesaikan: klaim ditolak')


@admin_bp.route('/conflicts/<int:claim_id>/notes', methods=['PUT'])
@jwt_required()
def update_conflict_notes(claim_id):
    user, err = require_admin()
    if err:
        return err

    claim = Claim.query.get_or_404(claim_id)
    data = request.get_json()
    claim.admin_notes = data.get('admin_notes', claim.admin_notes)
    if 'priority' in data:
        claim.priority = data['priority']
    db.session.commit()
    return success_response(data={'claim': claim.to_dict()}, message='Catatan diperbarui')


@admin_bp.route('/chart-data', methods=['GET'])
@jwt_required()
def chart_data():
    user, err = require_admin()
    if err:
        return err

    now = datetime.now(timezone.utc)

    # --- Weekly reports per day (last 7 days) ---
    # Build list: [Mon, Tue, Wed, Thu, Fri, Sat, Sun] of current week
    # We use the last 7 calendar days relative to today
    weekly_hilang = []
    weekly_ditemukan = []
    day_labels = []
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end   = (now - timedelta(days=i)).replace(hour=23, minute=59, second=59, microsecond=999999)
        h = Report.query.filter(
            Report.type == 'hilang',
            Report.created_at >= day_start,
            Report.created_at <= day_end
        ).count()
        d = Report.query.filter(
            Report.type == 'ditemukan',
            Report.created_at >= day_start,
            Report.created_at <= day_end
        ).count()
        weekly_hilang.append(h)
        weekly_ditemukan.append(d)
        # Short day label in Indonesian
        labels_id = ['Sen','Sel','Rab','Kam','Jum','Sab','Min']
        day_labels.append(labels_id[day_start.weekday()])

    # --- User growth last 7 days ---
    user_growth = []
    user_labels = []
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end   = (now - timedelta(days=i)).replace(hour=23, minute=59, second=59, microsecond=999999)
        count = User.query.filter(
            User.created_at >= day_start,
            User.created_at <= day_end
        ).count()
        user_growth.append(count)
        labels_id = ['Sen','Sel','Rab','Kam','Jum','Sab','Min']
        user_labels.append(labels_id[day_start.weekday()])

    # --- Category distribution (real counts) ---
    from app.models import Category
    categories = Category.query.filter_by(is_active=True).all()
    cat_data = []
    for cat in categories:
        count = Report.query.filter_by(category_id=cat.id, is_active=True).count()
        cat_data.append({'id': cat.id, 'name': cat.name, 'count': count})
    # Sort descending, take top 6
    cat_data.sort(key=lambda x: x['count'], reverse=True)
    cat_data = cat_data[:6]

    return success_response(data={
        'weekly_reports': {
            'labels': day_labels,
            'hilang': weekly_hilang,
            'ditemukan': weekly_ditemukan,
        },
        'user_growth': {
            'labels': user_labels,
            'values': user_growth,
        },
        'category_distribution': cat_data,
    })
