from datetime import datetime
import uuid
from . import db, GUID


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    project_name = db.Column(db.String(255), nullable=False)
    customer = db.Column(db.String(255))
    business_scheme = db.Column(db.String(100))
    status = db.Column(db.String(50))
    unit_kerja = db.Column(db.String(100))

    contract_value_idr = db.Column(db.Numeric(18, 2))
    contract_value_valas = db.Column(db.Numeric(18, 2))
    currency = db.Column(db.String(10))

    cogs_percent = db.Column(db.Numeric(5, 2))
    cogs_idr = db.Column(db.Numeric(18, 2))
    gpm_percent = db.Column(db.Numeric(5, 2))
    gpm_idr = db.Column(db.Numeric(18, 2))

    contract_signed_date = db.Column(db.Date)
    effective_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    duration_months = db.Column(db.Integer)
    after_sales_start = db.Column(db.Date)
    after_sales_end = db.Column(db.Date)

    project_leader = db.Column(db.String(100))
    project_analyst = db.Column(db.String(100))

    lkp_des_2025 = db.Column(db.Numeric(5, 2))
    target_rkap_2026 = db.Column(db.Numeric(5, 2))
    target_progress_2026 = db.Column(db.Numeric(5, 2))
    progress_achieved = db.Column(db.Numeric(5, 2))
    accumulated_progress = db.Column(db.Numeric(5, 2))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    milestones = db.relationship('ProjectMilestone', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    wbs_items = db.relationship('WbsItem', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    weekly_progress = db.relationship('WeeklyProgress', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    recovery_plans = db.relationship('RecoveryPlan', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    actions = db.relationship('ActionTracker', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    budget_controls = db.relationship('BudgetControl', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    budget_lines = db.relationship('BudgetDetailLine', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    cashflow_ins = db.relationship('CashflowIn', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    cashflow_outs = db.relationship('CashflowOut', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    procurements = db.relationship('ProcurementItem', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    proc_ops_list = db.relationship('ProcOpsStatus', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    proc_pol_list = db.relationship('ProcPolStatus', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    photos = db.relationship('ProjectPhoto', backref='project', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'project_code': self.project_code,
            'project_name': self.project_name,
            'customer': self.customer,
            'business_scheme': self.business_scheme,
            'status': self.status,
            'unit_kerja': self.unit_kerja,
            'contract_value_idr': float(self.contract_value_idr) if self.contract_value_idr else None,
            'contract_value_valas': float(self.contract_value_valas) if self.contract_value_valas else None,
            'currency': self.currency,
            'cogs_percent': float(self.cogs_percent) if self.cogs_percent else None,
            'cogs_idr': float(self.cogs_idr) if self.cogs_idr else None,
            'gpm_percent': float(self.gpm_percent) if self.gpm_percent else None,
            'gpm_idr': float(self.gpm_idr) if self.gpm_idr else None,
            'contract_signed_date': self.contract_signed_date.isoformat() if self.contract_signed_date else None,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'duration_months': self.duration_months,
            'after_sales_start': self.after_sales_start.isoformat() if self.after_sales_start else None,
            'after_sales_end': self.after_sales_end.isoformat() if self.after_sales_end else None,
            'project_leader': self.project_leader,
            'project_analyst': self.project_analyst,
            'lkp_des_2025': float(self.lkp_des_2025) if self.lkp_des_2025 else None,
            'target_rkap_2026': float(self.target_rkap_2026) if self.target_rkap_2026 else None,
            'target_progress_2026': float(self.target_progress_2026) if self.target_progress_2026 else None,
            'progress_achieved': float(self.progress_achieved) if self.progress_achieved else None,
            'accumulated_progress': float(self.accumulated_progress) if self.accumulated_progress else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ProjectMilestone(db.Model):
    __tablename__ = 'project_milestones'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(GUID(), db.ForeignKey('projects.id'), nullable=False)
    milestone_name = db.Column(db.String(255), nullable=False)
    milestone_category = db.Column(db.String(100))
    percentage = db.Column(db.Numeric(5, 2))
    target_date = db.Column(db.Date)
    is_cash_in = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(50))
    actual_date = db.Column(db.Date)
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'milestone_name': self.milestone_name,
            'milestone_category': self.milestone_category,
            'percentage': float(self.percentage) if self.percentage else None,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'is_cash_in': self.is_cash_in,
            'status': self.status,
            'actual_date': self.actual_date.isoformat() if self.actual_date else None,
            'notes': self.notes,
        }
