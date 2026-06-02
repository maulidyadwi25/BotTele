from datetime import datetime
import uuid
from . import db, GUID


class WbsItem(db.Model):
    __tablename__ = 'wbs_items'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(GUID(), db.ForeignKey('projects.id'), nullable=False)
    parent_id = db.Column(GUID(), db.ForeignKey('wbs_items.id'), nullable=True)

    wbs_number = db.Column(db.String(50))
    wbs_name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100))
    division = db.Column(db.String(100))
    pic_name = db.Column(db.String(100))
    activity_type = db.Column(db.String(10))

    contract_value = db.Column(db.Numeric(18, 2))
    weight_percent = db.Column(db.Numeric(5, 2))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    children = db.relationship('WbsItem', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    weekly_progress = db.relationship('WeeklyProgress', backref='wbs_item', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_children=False):
        result = {
            'id': self.id,
            'project_id': self.project_id,
            'parent_id': self.parent_id,
            'wbs_number': self.wbs_number,
            'wbs_name': self.wbs_name,
            'category': self.category,
            'division': self.division,
            'pic_name': self.pic_name,
            'activity_type': self.activity_type,
            'contract_value': float(self.contract_value) if self.contract_value else None,
            'weight_percent': float(self.weight_percent) if self.weight_percent else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_children:
            result['children'] = [c.to_dict() for c in self.children]
        return result
