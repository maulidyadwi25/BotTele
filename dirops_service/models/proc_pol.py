from datetime import datetime
import uuid
from . import db, GUID


class ProcPolStatus(db.Model):
    __tablename__ = 'proc_pol_status'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(GUID(), db.ForeignKey('projects.id'), nullable=False)

    request_id = db.Column(db.Integer)
    request_date = db.Column(db.Date)
    request_description = db.Column(db.Text)
    request_number = db.Column(db.String(50))
    project_code = db.Column(db.String(50))
    project_name = db.Column(db.String(255))
    project_manager = db.Column(db.String(100))
    work_unit_officer = db.Column(db.String(100))
    work_unit_email = db.Column(db.String(255))
    executor_name = db.Column(db.String(100))
    user_remarks = db.Column(db.Text)
    gm_feedback = db.Column(db.Text)
    request_status = db.Column(db.String(50))
    posting_date = db.Column(db.Date)

    rfp_number = db.Column(db.String(50))
    rfp_date = db.Column(db.Date)
    rfp_procurement_category = db.Column(db.String(100))
    rfp_company_name = db.Column(db.String(255))
    rfp_receiving_email = db.Column(db.String(255))
    rfp_department = db.Column(db.String(100))
    rfp_status = db.Column(db.String(50))

    hps_number = db.Column(db.String(50))
    hps_date = db.Column(db.Date)
    hps_currency = db.Column(db.String(10))
    hps_amount = db.Column(db.Numeric(18, 2))
    hps_item = db.Column(db.String(255))
    hps_status = db.Column(db.String(50))

    rks_number = db.Column(db.String(50))
    rks_date = db.Column(db.Date)
    rks_title = db.Column(db.String(255))
    rks_type = db.Column(db.String(100))
    rks_method = db.Column(db.String(100))
    rks_delivery_terms = db.Column(db.String(255))
    rks_delivery_time = db.Column(db.String(100))
    rks_payment_terms = db.Column(db.String(255))
    rks_currency = db.Column(db.String(10))
    rks_amount = db.Column(db.Numeric(18, 2))
    rks_status = db.Column(db.String(50))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'request_id': self.request_id,
            'request_date': self.request_date.isoformat() if self.request_date else None,
            'request_description': self.request_description,
            'request_number': self.request_number,
            'project_code': self.project_code,
            'project_name': self.project_name,
            'project_manager': self.project_manager,
            'request_status': self.request_status,
            'hps_amount': float(self.hps_amount) if self.hps_amount else None,
            'rks_amount': float(self.rks_amount) if self.rks_amount else None,
        }
