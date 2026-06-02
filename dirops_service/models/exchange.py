from datetime import datetime
import uuid
from . import db, GUID


class ExchangeRate(db.Model):
    __tablename__ = 'exchange_rates'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(GUID(), db.ForeignKey('projects.id'), nullable=True)

    currency_code = db.Column(db.String(10), nullable=False)
    rate = db.Column(db.Numeric(18, 2), nullable=False)
    effective_date = db.Column(db.Date, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('project_id', 'currency_code', 'effective_date', name='uq_exchange_rate'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'currency_code': self.currency_code,
            'rate': float(self.rate) if self.rate else None,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
        }
