from datetime import datetime
import uuid
from . import db, GUID


class BudgetControl(db.Model):
    __tablename__ = 'budget_controls'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(GUID(), db.ForeignKey('projects.id'), nullable=False)

    wbs_category = db.Column(db.String(100))
    remaining_budget_sap = db.Column(db.Numeric(18, 2))
    wbs_not_input = db.Column(db.Numeric(18, 2))
    total = db.Column(db.Numeric(18, 2))
    estimated_need = db.Column(db.Numeric(18, 2))
    difference = db.Column(db.Numeric(18, 2))
    difference_percent = db.Column(db.Numeric(5, 2))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'wbs_category': self.wbs_category,
            'remaining_budget_sap': float(self.remaining_budget_sap) if self.remaining_budget_sap else None,
            'wbs_not_input': float(self.wbs_not_input) if self.wbs_not_input else None,
            'total': float(self.total) if self.total else None,
            'estimated_need': float(self.estimated_need) if self.estimated_need else None,
            'difference': float(self.difference) if self.difference else None,
            'difference_percent': float(self.difference_percent) if self.difference_percent else None,
        }


class BudgetDetailLine(db.Model):
    __tablename__ = 'budget_detail_lines'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(GUID(), db.ForeignKey('projects.id'), nullable=False)

    wbs_object = db.Column(db.String(100))
    description = db.Column(db.String(255))
    budget = db.Column(db.Numeric(18, 2))
    actual = db.Column(db.Numeric(18, 2))
    commitment = db.Column(db.Numeric(18, 2))
    park_document = db.Column(db.Numeric(18, 2))
    remaining_order_plan = db.Column(db.Numeric(18, 2))
    assigned = db.Column(db.Numeric(18, 2))
    available = db.Column(db.Numeric(18, 2))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'wbs_object': self.wbs_object,
            'description': self.description,
            'budget': float(self.budget) if self.budget else None,
            'actual': float(self.actual) if self.actual else None,
            'commitment': float(self.commitment) if self.commitment else None,
            'park_document': float(self.park_document) if self.park_document else None,
            'remaining_order_plan': float(self.remaining_order_plan) if self.remaining_order_plan else None,
            'assigned': float(self.assigned) if self.assigned else None,
            'available': float(self.available) if self.available else None,
        }
