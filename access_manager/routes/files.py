"""File browser and permission management routes."""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, render_template, request, jsonify, session
from models import db
from models.user import FilePermission, TelegramUser
from utils.decorators import login_required
from services.permission_service import PermissionService
from services.drive_integration import DriveIntegration

files_bp = Blueprint('files', __name__, url_prefix='/files')


@files_bp.route('/', methods=['GET'])
@login_required
def index():
    """File browser page."""
    folder_id = request.args.get('folder_id', os.getenv('FOLDER_ID', ''))
    return render_template('files.html', folder_id=folder_id)


@files_bp.route('/api', methods=['GET'])
@login_required
def api_list():
    """API: List files from Google Drive."""
    folder_id = request.args.get('folder_id', os.getenv('FOLDER_ID', ''))
    
    di = DriveIntegration()
    files = di.list_files(folder_id)
    
    return jsonify({'success': True, 'data': files})


@files_bp.route('/api/<file_id>/permissions', methods=['GET'])
@login_required
def api_get_permissions(file_id):
    """API: Get permissions for a specific file."""
    ps = PermissionService()
    permissions = ps.get_file_permissions(file_id)
    return jsonify({'success': True, 'data': permissions})


@files_bp.route('/api/<file_id>/permissions', methods=['PUT'])
@login_required
def api_update_permissions(file_id):
    """API: Update permissions for a file."""
    data = request.get_json()
    file_name = data.get('file_name', 'Unknown')
    permissions = data.get('permissions', [])

    ps = PermissionService()
    admin_id = session.get('user_id')
    result = ps.update_file_permissions(file_id, file_name, permissions, admin_id)

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


@files_bp.route('/api/permissions/bulk', methods=['POST'])
@login_required
def api_bulk_permissions():
    """API: Bulk update permissions."""
    data = request.get_json()
    updates = data.get('updates', [])

    ps = PermissionService()
    admin_id = session.get('user_id')
    result = ps.bulk_update_permissions(updates, admin_id)

    return jsonify(result)
