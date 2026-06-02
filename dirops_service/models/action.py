from datetime import datetime
import uuid
from . import db, GUID


class ActionTracker(db.Model):
    __tablename__ = 'action_trackers'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(GUID(), db.ForeignKey('projects.id'), nullable=False)

    ref_number = db.Column(db.Integer)
    action_description = db.Column(db.Text)
    organization_responsible = db.Column(db.String(100))
    actionee = db.Column(db.String(100))
    open_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    due_day = db.Column(db.Integer)
    status = db.Column(db.String(20))
    case_description = db.Column(db.Text)
    update_notes = db.Column(db.Text)
    reference = db.Column(db.String(255))
    priority = db.Column(db.String(20))
    critical_issue_date = db.Column(db.Date)
    critical_issue = db.Column(db.Text)
    impact = db.Column(db.Text)
    action_plan = db.Column(db.Text)
    high_level_support = db.Column(db.Text)
    high_level_action_plan = db.Column(db.Text)
    pmo_recommendation = db.Column(db.Text)
    closed_date = db.Column(db.Date)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.Index('ix_action_trackers_project_status', 'project_id', 'status'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'ref_number': self.ref_number,
            'action_description': self.action_description,
            'organization_responsible': self.organization_responsible,
            'actionee': self.actionee,
            'open_date': self.open_date.isoformat() if self.open_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'due_day': self.due_day,
            'status': self.status,
            'case_description': self.case_description,
            'update_notes': self.update_notes,
            'reference': self.reference,
            'priority': self.priority,
            'critical_issue_date': self.critical_issue_date.isoformat() if self.critical_issue_date else None,
            'critical_issue': self.critical_issue,
            'impact': self.impact,
            'action_plan': self.action_plan,
            'high_level_support': self.high_level_support,
            'high_level_action_plan': self.high_level_action_plan,
            'pmo_recommendation': self.pmo_recommendation,
            'closed_date': self.closed_date.isoformat() if self.closed_date else None,
            'is_overdue': self.due_day < 0 if self.due_day else False,
        }
