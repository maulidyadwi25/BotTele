"""Dashboard routes."""
from flask import Blueprint, render_template
from utils.decorators import login_required
from services.permission_service import PermissionService

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Dashboard page."""
    ps = PermissionService()
    stats = ps.get_dashboard_stats()
    recent_activity = ps.get_recent_activity()
    return render_template('dashboard.html', stats=stats, recent_activity=recent_activity)
