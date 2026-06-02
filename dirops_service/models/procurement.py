from datetime import datetime
import uuid
from . import db, GUID


class ProcurementItem(db.Model):
    __tablename__ = 'procurement_items'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(GUID(), db.ForeignKey('projects.id'), nullable=False)
    vendor_id = db.Column(GUID(), db.ForeignKey('vendors.id'), nullable=True)

    procurement_name = db.Column(db.String(255))
    target_date = db.Column(db.Date)
    status = db.Column(db.String(50))
    progress = db.Column(db.Numeric(5, 2))
    priority = db.Column(db.String(20))
    procurement_type = db.Column(db.String(100))
    payment_type = db.Column(db.String(100))
    procurement_policy = db.Column(db.String(100))

    hps_value = db.Column(db.Numeric(18, 2))
    hps_date = db.Column(db.Date)
    rks_value = db.Column(db.Numeric(18, 2))
    rks_date = db.Column(db.Date)
    ome_value = db.Column(db.Numeric(18, 2))

    pr_number = db.Column(db.String(50))
    proc_ops = db.Column(db.String(100))
    po_number = db.Column(db.String(50))
    contract_value = db.Column(db.Numeric(18, 2))
    currency = db.Column(db.String(10))
    efficiency = db.Column(db.Numeric(5, 2))

    due_date = db.Column(db.Date)
    estimated_delivery = db.Column(db.Date)
    delivery_status = db.Column(db.String(50))
    payment_status = db.Column(db.String(50))

    sph_count = db.Column(db.Integer, default=0)
    hps_count = db.Column(db.Integer, default=0)
    rks_count = db.Column(db.Integer, default=0)
    pr_count = db.Column(db.Integer, default=0)
    rfq_count = db.Column(db.Integer, default=0)
    negotiation_count = db.Column(db.Integer, default=0)
    po_count = db.Column(db.Integer, default=0)
    kontrak_count = db.Column(db.Integer, default=0)
    production_count = db.Column(db.Integer, default=0)
    delivered_count = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    payments = db.relationship('ProcurementPayment', backref='procurement_item', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'vendor_id': self.vendor_id,
            'vendor_name': self.vendor.vendor_name if self.vendor else None,
            'procurement_name': self.procurement_name,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'status': self.status,
            'progress': float(self.progress) if self.progress else None,
            'priority': self.priority,
            'procurement_type': self.procurement_type,
            'payment_type': self.payment_type,
            'procurement_policy': self.procurement_policy,
            'hps_value': float(self.hps_value) if self.hps_value else None,
            'rks_value': float(self.rks_value) if self.rks_value else None,
            'contract_value': float(self.contract_value) if self.contract_value else None,
            'currency': self.currency,
            'efficiency': float(self.efficiency) if self.efficiency else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'delivery_status': self.delivery_status,
            'payment_status': self.payment_status,
        }


class ProcurementPayment(db.Model):
    __tablename__ = 'procurement_payments'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    procurement_item_id = db.Column(GUID(), db.ForeignKey('procurement_items.id'), nullable=False)

    payment_term_number = db.Column(db.Integer)
    payment_type = db.Column(db.String(50))
    submit_date = db.Column(db.Date)
    amount = db.Column(db.Numeric(18, 2))
    gr_ses = db.Column(db.String(50))
    no_spp = db.Column(db.String(50))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'procurement_item_id': self.procurement_item_id,
            'payment_term_number': self.payment_term_number,
            'payment_type': self.payment_type,
            'submit_date': self.submit_date.isoformat() if self.submit_date else None,
            'amount': float(self.amount) if self.amount else None,
            'gr_ses': self.gr_ses,
            'no_spp': self.no_spp,
        }
