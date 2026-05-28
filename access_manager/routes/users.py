"""User management routes."""
from flask import Blueprint, render_template, request, jsonify, session
from models import db
from models.user import TelegramUser, UserGlobalAccess, AdminUser
from utils.decorators import login_required
from services.permission_service import PermissionService

users_bp = Blueprint('users', __name__, url_prefix='/users')


@users_bp.route('/', methods=['GET'])
@login_required
def index():
    """User management page."""
    ps = PermissionService()
    users = ps.get_all_users()
    stats = ps.get_user_stats()
    return render_template('users.html', users=users, stats=stats)


@users_bp.route('/api', methods=['GET'])
@login_required
def api_list():
    """API: List all users."""
    ps = PermissionService()
    users = ps.get_all_users()
    return jsonify({'success': True, 'data': users})


@users_bp.route('/api', methods=['POST'])
@login_required
def api_create():
    """API: Create new Telegram user.
    
    Either telegram_id OR username must be provided (at least one required).
    """
    data = request.get_json() or {}
    
    telegram_id = (data.get('telegram_id') or '').strip()
    username = (data.get('username') or '').strip()
    display_name = (data.get('display_name') or '').strip()

    # Validate: at least one of telegram_id or username must be provided
    if not telegram_id and not username:
        return jsonify({'success': False, 'error': 'Telegram ID or Username is required (at least one)'}), 400

    ps = PermissionService()
    result = ps.create_user(telegram_id if telegram_id else None,
                           username if username else None,
                           display_name)

    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 400


@users_bp.route('/api/<int:user_id>', methods=['PUT'])
@login_required
def api_update(user_id):
    """API: Update Telegram user."""
    data = request.get_json()
    ps = PermissionService()
    result = ps.update_user(user_id, data)

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


@users_bp.route('/api/<int:user_id>', methods=['DELETE'])
@login_required
def api_delete(user_id):
    """API: Delete Telegram user."""
    ps = PermissionService()
    result = ps.delete_user(user_id)

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


@users_bp.route('/api/<int:user_id>/toggle-global', methods=['POST'])
@login_required
def api_toggle_global(user_id):
    """API: Toggle global access for a user."""
    ps = PermissionService()
    result = ps.toggle_global_access(user_id)

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


@users_bp.route('/api/<int:user_id>/toggle-status', methods=['POST'])
@login_required
def api_toggle_status(user_id):
    """API: Toggle user status (active/suspended)."""
    ps = PermissionService()
    result = ps.toggle_user_status(user_id)

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


