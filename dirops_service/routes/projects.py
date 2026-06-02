from flask import Blueprint, jsonify, request
from ..models import db, Project, WbsItem, ActionTracker, BudgetControl
from sqlalchemy import func

projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')


@projects_bp.route('', methods=['GET'])
def list_projects():
    projects = Project.query.all()
    return jsonify([p.to_dict() for p in projects])


@projects_bp.route('/<project_id>', methods=['GET'])
def get_project(project_id):
    project = Project.query.get_or_404(project_id)
    return jsonify(project.to_dict())


@projects_bp.route('/<project_id>/summary', methods=['GET'])
def project_summary(project_id):
    project = Project.query.get_or_404(project_id)

    open_actions = ActionTracker.query.filter_by(project_id=project_id, status='OPEN').count()
    closed_actions = ActionTracker.query.filter_by(project_id=project_id, status='CLOSED').count()
    overdue_actions = ActionTracker.query.filter(
        ActionTracker.project_id == project_id,
        ActionTracker.status == 'OPEN',
        ActionTracker.due_day < 0
    ).count()

    budget = BudgetControl.query.filter_by(project_id=project_id).first()

    summary = {
        'project_code': project.project_code,
        'project_name': project.project_name,
        'customer': project.customer,
        'status': project.status,
        'contract_value_idr': float(project.contract_value_idr) if project.contract_value_idr else None,
        'progress_achieved': float(project.progress_achieved) if project.progress_achieved else None,
        'target_progress_2026': float(project.target_progress_2026) if project.target_progress_2026 else None,
        'accumulated_progress': float(project.accumulated_progress) if project.accumulated_progress else None,
        'open_actions': open_actions,
        'closed_actions': closed_actions,
        'overdue_actions': overdue_actions,
        'total_actions': open_actions + closed_actions,
        'remaining_budget': float(budget.remaining_budget_sap) if budget and budget.remaining_budget_sap else None,
        'estimated_need': float(budget.estimated_need) if budget and budget.estimated_need else None,
        'budget_difference': float(budget.difference) if budget and budget.difference else None,
    }
    return jsonify(summary)


@projects_bp.route('/<project_id>/actions', methods=['GET'])
def project_actions(project_id):
    status = request.args.get('status')
    query = ActionTracker.query.filter_by(project_id=project_id)
    if status:
        query = query.filter_by(status=status)
    actions = query.all()
    return jsonify([a.to_dict() for a in actions])


@projects_bp.route('/<project_id>/wbs', methods=['GET'])
def project_wbs(project_id):
    wbs_items = WbsItem.query.filter_by(project_id=project_id).all()
    return jsonify([w.to_dict(include_children=True) for w in wbs_items])
