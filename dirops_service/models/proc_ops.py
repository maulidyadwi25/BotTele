from datetime import datetime
import uuid
from . import db, GUID


class ProcOpsStatus(db.Model):
    __tablename__ = 'proc_ops_status'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(GUID(), db.ForeignKey('projects.id'), nullable=False)

    proc_ops_id = db.Column(db.Integer)
    officer = db.Column(db.String(100))
    pr_number = db.Column(db.String(50))
    po_manual = db.Column(db.String(50))
    po_sap = db.Column(db.String(50))
    description = db.Column(db.Text)
    supplier = db.Column(db.String(255))
    amount = db.Column(db.Numeric(18, 2))
    currency = db.Column(db.String(10))
    delivery_time = db.Column(db.Date)
    project_name = db.Column(db.String(255))
    user_name = db.Column(db.String(100))
    status = db.Column(db.String(50))
    follow_up = db.Column(db.Text)
    deadline = db.Column(db.Date)
    issue = db.Column(db.Text)
    project_code = db.Column(db.String(50))
    status_2 = db.Column(db.String(50))
    k3 = db.Column(db.String(50))
    k4 = db.Column(db.String(50))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'proc_ops_id': self.proc_ops_id,
            'officer': self.officer,
            'pr_number': self.pr_number,
            'po_manual': self.po_manual,
            'po_sap': self.po_sap,
            'description': self.description,
            'supplier': self.supplier,
            'amount': float(self.amount) if self.amount else None,
            'currency': self.currency,
            'delivery_time': self.delivery_time.isoformat() if self.delivery_time else None,
            'project_name': self.project_name,
            'user_name': self.user_name,
            'status': self.status,
            'follow_up': self.follow_up,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'issue': self.issue,
            'project_code': self.project_code,
            'status_2': self.status_2,
            'k3': self.k3,
            'k4': self.k4,
        }
