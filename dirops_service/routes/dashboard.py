from flask import Blueprint, jsonify
from ..models import db, Project, ActionTracker, BudgetControl, CashflowIn, CashflowOut

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('/summary')
def summary():
    total_projects = Project.query.count()
    active_projects = Project.query.filter_by(status='CARRY OVER').count()

    open_actions = ActionTracker.query.filter_by(status='OPEN').count()
    closed_actions = ActionTracker.query.filter_by(status='CLOSED').count()
    overdue_actions = ActionTracker.query.filter(
        ActionTracker.status == 'OPEN',
        ActionTracker.due_day < 0
    ).count()

    total_cashflow_in = db.session.query(func.sum(CashflowIn.amount)).scalar() or 0
    total_cashflow_out = db.session.query(func.sum(CashflowOut.amount)).scalar() or 0

    return jsonify({
        'total_projects': total_projects,
        'active_projects': active_projects,
        'open_actions': open_actions,
        'closed_actions': closed_actions,
        'overdue_actions': overdue_actions,
        'total_cashflow_in': float(total_cashflow_in),
        'total_cashflow_out': float(total_cashflow_out),
    })
