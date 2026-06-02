from datetime import datetime
import uuid
from . import db, GUID


class WeeklyProgress(db.Model):
    __tablename__ = 'weekly_progress'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(GUID(), db.ForeignKey('projects.id'), nullable=False)
    wbs_id = db.Column(GUID(), db.ForeignKey('wbs_items.id'), nullable=True)

    year = db.Column(db.Integer, nullable=False)
    week_number = db.Column(db.Integer, nullable=False)
    week_label = db.Column(db.String(20))
    week_start_date = db.Column(db.Date)

    plan_value = db.Column(db.Numeric(5, 2))
    actual_value = db.Column(db.Numeric(5, 2))
    accumulated_plan = db.Column(db.Numeric(5, 2))
    accumulated_actual = db.Column(db.Numeric(5, 2))
    deviation = db.Column(db.Numeric(5, 2))
    revenue_value = db.Column(db.Numeric(18, 2))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('project_id', 'wbs_id', 'year', 'week_number', name='uq_weekly_progress'),
        db.Index('ix_weekly_progress_project_year_week', 'project_id', 'year', 'week_number'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'wbs_id': self.wbs_id,
            'year': self.year,
            'week_number': self.week_number,
            'week_label': self.week_label,
            'week_start_date': self.week_start_date.isoformat() if self.week_start_date else None,
            'plan_value': float(self.plan_value) if self.plan_value else None,
            'actual_value': float(self.actual_value) if self.actual_value else None,
            'accumulated_plan': float(self.accumulated_plan) if self.accumulated_plan else None,
            'accumulated_actual': float(self.accumulated_actual) if self.accumulated_actual else None,
            'deviation': float(self.deviation) if self.deviation else None,
            'revenue_value': float(self.revenue_value) if self.revenue_value else None,
        }
