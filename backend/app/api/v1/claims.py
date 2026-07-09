from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone, timedelta

from app.extensions import db
from app.models import Claim, Report, User, Notification
from app.utils.response import success_response, error_response, paginated_response

claims_bp = Blueprint('claims', __name__, url_prefix='/api/v1/claims')


@claims_bp.route('', methods=['POST'])
@jwt_required()
def create_claim():
    """A user submits a claim of ownership on a report (answering the secret feature)."""
    user_id = int(get_jwt_identity())
    data = request.get_json()

    report_id = data.get('report_id')
    answer = data.get('answer', '').strip()

    if not report_id or not answer:
        return error_response('report_id and answer are required', 400)

    report = Report.query.get_or_404(report_id)

    if report.user_id == user_id:
        return error_response('Cannot claim your own report', 400)

    existing = Claim.query.filter_by(report_id=report_id, claimant_id=user_id).first()
    if existing:
        return error_response('You already submitted a claim for this report', 409)

    claim = Claim(
        report_id=report_id,
        claimant_id=user_id,
        answer=answer,
        deadline=datetime.now(timezone.utc) + timedelta(days=2),
    )
    db.session.add(claim)

    # Mark report as in process and notify owner
    report.status = 'proses'
    notif = Notification(
        user_id=report.user_id,
        actor_id=user_id,
        type='claim',
        title='Ada klaim baru pada laporanmu',
        message=f'Seseorang mengklaim kepemilikan atas "{report.title}"',
        data={'report_id': report.id, 'claim_id': None}
    )
    db.session.add(notif)
    db.session.commit()

    return success_response(data={'claim': claim.to_dict()}, message='Klaim berhasil diajukan',
                             status_code=201)


@claims_bp.route('/my', methods=['GET'])
@jwt_required()
def my_claims():
    user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    query = Claim.query.filter_by(claimant_id=user_id)
    total = query.count()
    claims = query.order_by(Claim.created_at.desc()).offset((page-1)*per_page).limit(per_page).all()

    return paginated_response(items=[c.to_dict() for c in claims], total=total, page=page, per_page=per_page)


@claims_bp.route('/report/<int:report_id>', methods=['GET'])
@jwt_required()
def claims_for_report(report_id):
    """Report owner views all claims submitted against their report."""
    user_id = int(get_jwt_identity())
    report = Report.query.get_or_404(report_id)
    user = User.query.get(user_id)

    if report.user_id != user_id and (not user or user.role != 'admin'):
        return error_response('Forbidden', 403)

    claims = Claim.query.filter_by(report_id=report_id).order_by(Claim.created_at.desc()).all()
    return success_response(data={'claims': [c.to_dict() for c in claims]})


@claims_bp.route('/<int:claim_id>/approve', methods=['POST'])
@jwt_required()
def approve_claim(claim_id):
    user_id = int(get_jwt_identity())
    claim = Claim.query.get_or_404(claim_id)
    user = User.query.get(user_id)

    is_owner = claim.report.user_id == user_id
    is_admin = user and user.role == 'admin'
    if not is_owner and not is_admin:
        return error_response('Forbidden', 403)

    claim.status = 'approved'
    claim.resolved_by = user_id
    claim.resolved_at = datetime.now(timezone.utc)
    claim.handover_status = 'menunggu_metode'
    # Status laporan tetap 'proses' (bukan 'selesai') sampai serah terima fisik
    # benar-benar dikonfirmasi lewat endpoint handover-complete.
    claim.report.status = 'proses'

    # Reject other pending claims on the same report
    Claim.query.filter(
        Claim.report_id == claim.report_id,
        Claim.id != claim.id,
        Claim.status.in_(['pending', 'disputed'])
    ).update({'status': 'rejected', 'resolved_by': user_id,
              'resolved_at': datetime.now(timezone.utc)}, synchronize_session=False)

    claimant = User.query.get(claim.claimant_id)
    if claimant:
        claimant.total_found = (claimant.total_found or 0) + 1

    notif = Notification(
        user_id=claim.claimant_id,
        type='claim_approved',
        title='Klaim disetujui!',
        message=f'Klaim Anda atas "{claim.report.title}" telah disetujui. Lanjutkan ke proses serah terima.',
        data={'report_id': claim.report_id, 'claim_id': claim.id}
    )
    db.session.add(notif)
    db.session.commit()

    return success_response(data={'claim': claim.to_dict()}, message='Klaim disetujui')


@claims_bp.route('/<int:claim_id>/reject', methods=['POST'])
@jwt_required()
def reject_claim(claim_id):
    user_id = int(get_jwt_identity())
    claim = Claim.query.get_or_404(claim_id)
    user = User.query.get(user_id)

    is_owner = claim.report.user_id == user_id
    is_admin = user and user.role == 'admin'
    if not is_owner and not is_admin:
        return error_response('Forbidden', 403)

    claim.status = 'rejected'
    claim.resolved_by = user_id
    claim.resolved_at = datetime.now(timezone.utc)

    notif = Notification(
        user_id=claim.claimant_id,
        type='claim_rejected',
        title='Klaim ditolak',
        message=f'Klaim Anda atas "{claim.report.title}" tidak dapat diverifikasi',
        data={'report_id': claim.report_id}
    )
    db.session.add(notif)
    db.session.commit()

    return success_response(data={'claim': claim.to_dict()}, message='Klaim ditolak')


@claims_bp.route('/<int:claim_id>/dispute', methods=['POST'])
@jwt_required()
def dispute_claim(claim_id):
    """Escalate a claim to admin for conflict resolution (e.g. multiple competing claims)."""
    user_id = int(get_jwt_identity())
    claim = Claim.query.get_or_404(claim_id)

    if claim.report.user_id != user_id:
        return error_response('Forbidden', 403)

    claim.status = 'disputed'
    claim.priority = request.get_json().get('priority', 'tinggi') if request.is_json else 'tinggi'
    db.session.commit()

    return success_response(data={'claim': claim.to_dict()}, message='Sengketa dieskalasi ke admin')


@claims_bp.route('/<int:claim_id>', methods=['GET'])
@jwt_required()
def get_claim(claim_id):
    """Get a single claim's detail, used to drive the handover status page."""
    user_id = int(get_jwt_identity())
    claim = Claim.query.get_or_404(claim_id)
    user = User.query.get(user_id)

    is_owner = claim.report.user_id == user_id
    is_claimant = claim.claimant_id == user_id
    is_admin = user and user.role == 'admin'
    if not is_owner and not is_claimant and not is_admin:
        return error_response('Forbidden', 403)

    return success_response(data={'claim': claim.to_dict()})


@claims_bp.route('/<int:claim_id>/handover-method', methods=['PUT'])
@jwt_required()
def set_handover_method(claim_id):
    """Either party (owner or claimant) selects the handover method after a claim is approved."""
    user_id = int(get_jwt_identity())
    claim = Claim.query.get_or_404(claim_id)

    is_owner = claim.report.user_id == user_id
    is_claimant = claim.claimant_id == user_id
    if not is_owner and not is_claimant:
        return error_response('Forbidden', 403)

    if claim.status != 'approved':
        return error_response('Klaim belum disetujui, serah terima belum dapat diatur', 400)

    data = request.get_json() or {}
    method = data.get('method')
    if method not in ('cod', 'titik_aman', 'kurir'):
        return error_response('Metode serah terima tidak valid', 400)

    claim.handover_method = method
    claim.handover_location = data.get('location') if method == 'titik_aman' else None
    claim.handover_tracking = data.get('tracking') if method == 'kurir' else None
    claim.handover_status = 'dalam_proses'
    db.session.commit()

    # Notify the other party
    other_user_id = claim.claimant_id if is_owner else claim.report.user_id
    notif = Notification(
        user_id=other_user_id,
        actor_id=user_id,
        type='handover_update',
        title='Metode serah terima dipilih',
        message=f'Metode serah terima untuk "{claim.report.title}" telah diatur',
        data={'report_id': claim.report_id, 'claim_id': claim.id}
    )
    db.session.add(notif)
    db.session.commit()

    return success_response(data={'claim': claim.to_dict()}, message='Metode serah terima disimpan')


@claims_bp.route('/<int:claim_id>/handover-complete', methods=['POST'])
@jwt_required()
def complete_handover(claim_id):
    """Mark the handover as fully completed - typically done by the original owner
    once they've physically received the item back."""
    user_id = int(get_jwt_identity())
    claim = Claim.query.get_or_404(claim_id)

    if claim.report.user_id != user_id:
        return error_response('Hanya pemilik laporan yang dapat menyelesaikan serah terima', 403)

    if claim.handover_status != 'dalam_proses':
        return error_response('Serah terima belum dalam proses', 400)

    claim.handover_status = 'selesai'
    claim.handover_completed_at = datetime.now(timezone.utc)
    claim.report.status = 'selesai'

    notif = Notification(
        user_id=claim.claimant_id,
        type='handover_complete',
        title='Serah terima selesai',
        message=f'Barang "{claim.report.title}" telah berhasil dikembalikan',
        data={'report_id': claim.report_id, 'claim_id': claim.id}
    )
    db.session.add(notif)
    db.session.commit()

    return success_response(data={'claim': claim.to_dict()}, message='Serah terima selesai')
