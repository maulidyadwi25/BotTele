"""
Database query service for DirOps - queries data directly from database instead of Excel sheets.
"""
from typing import Optional, Dict, List, Any
from sqlalchemy import func

# Lazy import to avoid circular imports
_db = None
_models = None


def _get_db_and_models():
    """Lazy initialization of database and models."""
    global _db, _models
    if _db is None:
        from dirops_service.database import create_app
        from dirops_service.models import (
            db, Project, BudgetControl, BudgetDetailLine,
            CashflowIn, CashflowOut, ActionTracker, WbsItem
        )
        _db = create_app()
        _models = {
            'db': db,
            'Project': Project,
            'BudgetControl': BudgetControl,
            'BudgetDetailLine': BudgetDetailLine,
            'CashflowIn': CashflowIn,
            'CashflowOut': CashflowOut,
            'ActionTracker': ActionTracker,
            'WbsItem': WbsItem
        }
    return _db, _models


def get_project_by_code(project_code: str) -> Optional[Dict]:
    """Get project info by project code."""
    app, db = _get_db_and_models()
    Project = _models['Project']
    
    with app.app_context():
        project = Project.query.filter_by(project_code=project_code).first()
        if project:
            return project.to_dict()
        return None


def get_project_budget_summary(project_code: str) -> Optional[Dict]:
    """Get budget summary for a project from database."""
    app, db = _get_db_and_models()
    Project = _models['Project']
    BudgetControl = _models['BudgetControl']
    
    with app.app_context():
        project = Project.query.filter_by(project_code=project_code).first()
        if not project:
            return None
        
        budget_controls = BudgetControl.query.filter_by(project_id=project.id).all()
        
        if not budget_controls:
            return {
                'project_code': project_code,
                'project_name': project.project_name,
                'has_budget_data': False,
                'message': 'Data budget belum tersedia di database'
            }
        
        # Aggregate budget data
        total_remaining = sum(float(b.remaining_budget_sap or 0) for b in budget_controls)
        total_wbs_not_input = sum(float(b.wbs_not_input or 0) for b in budget_controls)
        total = sum(float(b.total or 0) for b in budget_controls)
        total_estimated = sum(float(b.estimated_need or 0) for b in budget_controls)
        total_difference = sum(float(b.difference or 0) for b in budget_controls)
        
        return {
            'project_code': project_code,
            'project_name': project.project_name,
            'has_budget_data': True,
            'total_budget': total,
            'remaining_budget_sap': total_remaining,
            'wbs_not_input': total_wbs_not_input,
            'estimated_need': total_estimated,
            'difference': total_difference,
            'budget_lines': len(budget_controls)
        }


def get_project_contract_value(project_code: str) -> Optional[Dict]:
    """Get contract value info for a project."""
    app, db = _get_db_and_models()
    Project = _models['Project']
    
    with app.app_context():
        project = Project.query.filter_by(project_code=project_code).first()
        if not project:
            return None
        
        return {
            'project_code': project_code,
            'project_name': project.project_name,
            'contract_value_idr': float(project.contract_value_idr) if project.contract_value_idr else None,
            'contract_value_valas': project.contract_value_valas,
            'currency': project.currency,
            'customer': project.customer,
            'status': project.status,
            'progress_achieved': float(project.progress_achieved) if project.progress_achieved else None
        }


def get_project_summary(project_code: str) -> Optional[Dict]:
    """Get full project summary including budget, actions, and progress."""
    app, db = _get_db_and_models()
    Project = _models['Project']
    BudgetControl = _models['BudgetControl']
    ActionTracker = _models['ActionTracker']
    
    with app.app_context():
        project = Project.query.filter_by(project_code=project_code).first()
        if not project:
            return None
        
        # Get budget
        budget_controls = BudgetControl.query.filter_by(project_id=project.id).all()
        total_budget = sum(float(b.total or 0) for b in budget_controls) if budget_controls else None
        remaining_budget = sum(float(b.remaining_budget_sap or 0) for b in budget_controls) if budget_controls else None
        
        # Get action stats
        open_actions = ActionTracker.query.filter_by(project_id=project.id, status='OPEN').count()
        closed_actions = ActionTracker.query.filter_by(project_id=project.id, status='CLOSED').count()
        overdue_actions = ActionTracker.query.filter(
            ActionTracker.project_id == project.id,
            ActionTracker.status == 'OPEN',
            ActionTracker.due_day < 0
        ).count()
        
        return {
            'project_code': project_code,
            'project_name': project.project_name,
            'customer': project.customer,
            'status': project.status,
            'contract_value_idr': float(project.contract_value_idr) if project.contract_value_idr else None,
            'progress_achieved': float(project.progress_achieved) if project.progress_achieved else None,
            'target_progress_2026': float(project.target_progress_2026) if project.target_progress_2026 else None,
            'total_budget': total_budget,
            'remaining_budget': remaining_budget,
            'open_actions': open_actions,
            'closed_actions': closed_actions,
            'overdue_actions': overdue_actions,
            'total_actions': open_actions + closed_actions
        }


def format_currency(amount: float, currency: str = 'IDR') -> str:
    """Format currency for display."""
    if amount is None:
        return 'N/A'
    
    if currency == 'IDR':
        # Format as IDR: 1,000,000,000
        return f"Rp {amount:,.0f}".replace(',', '.')
    else:
        return f"{amount:,.2f} {currency}"


def get_budget_summary_text(project_code: str) -> str:
    """Get formatted budget summary text for a project."""
    summary = get_project_budget_summary(project_code)
    
    if not summary:
        return f"Proyek {project_code} tidak ditemukan."
    
    if not summary.get('has_budget_data'):
        return f"📊 **Budget Summary - {summary['project_name']}**\n\nData budget belum tersedia di database."
    
    lines = [
        f"📊 **Budget Summary - {summary['project_name']}**",
        f"",
        f"💰 Total Budget: {format_currency(summary['total_budget'])}",
        f"💵 Sisa Anggaran SAP: {format_currency(summary['remaining_budget_sap'])}",
        f"📝 WBS Belum Input: {format_currency(summary['wbs_not_input'])}",
        f"📈 Estimasi Kebutuhan: {format_currency(summary['estimated_need'])}",
        f"📉 Selisih: {format_currency(summary['difference'])}",
    ]
    
    return "\n".join(lines)
