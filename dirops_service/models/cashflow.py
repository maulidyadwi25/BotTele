from datetime import datetime
import uuid
from . import db, GUID


class CashflowIn(db.Model):
    __tablename__ = 'cashflow_in'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(GUID(), db.ForeignKey('projects.id'), nullable=False)

    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    month_label = db.Column(db.String(20))
    amount = db.Column(db.Numeric(18, 2))
    description = db.Column(db.String(255))
    no_nota = db.Column(db.String(50))
    no_spp = db.Column(db.String(50))
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.Index('ix_cashflow_in_project_year_month', 'project_id', 'year', 'month'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'year': self.year,
            'month': self.month,
            'month_label': self.month_label,
            'amount': float(self.amount) if self.amount else None,
            'description': self.description,
            'no_nota': self.no_nota,
            'no_spp': self.no_spp,
            'notes': self.notes,
        }


class CashflowOut(db.Model):
    __tablename__ = 'cashflow_out'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(GUID(), db.ForeignKey('projects.id'), nullable=False)
    vendor_id = db.Column(GUID(), db.ForeignKey('vendors.id'), nullable=True)

    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    month_label = db.Column(db.String(20))
    amount = db.Column(db.Numeric(18, 2))
    description = db.Column(db.String(255))
    no_nota = db.Column(db.String(50))
    no_spp = db.Column(db.String(50))
    payment_status = db.Column(db.String(50))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vendor = db.relationship('Vendor', backref='cashflow_outs')

    __table_args__ = (
        db.Index('ix_cashflow_out_project_year_month', 'project_id', 'year', 'month'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'vendor_id': self.vendor_id,
            'year': self.year,
            'month': self.month,
            'month_label': self.month_label,
            'amount': float(self.amount) if self.amount else None,
            'description': self.description,
            'no_nota': self.no_nota,
            'no_spp': self.no_spp,
            'payment_status': self.payment_status,
            'vendor_name': self.vendor.vendor_name if self.vendor else None,
        }
