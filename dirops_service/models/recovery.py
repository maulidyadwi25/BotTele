from datetime import datetime
import uuid
from . import db, GUID


class RecoveryPlan(db.Model):
    __tablename__ = 'recovery_plans'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(GUID(), db.ForeignKey('projects.id'), nullable=False)

    year = db.Column(db.Integer, nullable=False)
    week_number = db.Column(db.Integer, nullable=False)
    week_label = db.Column(db.String(20))

    target_rkap = db.Column(db.Numeric(5, 2))
    target_project = db.Column(db.Numeric(5, 2))
    realization = db.Column(db.Numeric(5, 2))
    deviation = db.Column(db.Numeric(5, 2))
    recovery_plan_percent = db.Column(db.Numeric(5, 2))
    recovery_plan_description = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'year': self.year,
            'week_number': self.week_number,
            'week_label': self.week_label,
            'target_rkap': float(self.target_rkap) if self.target_rkap else None,
            'target_project': float(self.target_project) if self.target_project else None,
            'realization': float(self.realization) if self.realization else None,
            'deviation': float(self.deviation) if self.deviation else None,
            'recovery_plan_percent': float(self.recovery_plan_percent) if self.recovery_plan_percent else None,
            'recovery_plan_description': self.recovery_plan_description,
        }
