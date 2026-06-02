from datetime import datetime
import uuid
from . import db, GUID


class Vendor(db.Model):
    __tablename__ = 'vendors'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    vendor_code = db.Column(db.String(50), unique=True)
    vendor_name = db.Column(db.String(255), nullable=False)
    vendor_type = db.Column(db.String(100))
    country = db.Column(db.String(100))
    contact_email = db.Column(db.String(255))
    contact_phone = db.Column(db.String(50))
    address = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    procurements = db.relationship('ProcurementItem', backref='vendor', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'vendor_code': self.vendor_code,
            'vendor_name': self.vendor_name,
            'vendor_type': self.vendor_type,
            'country': self.country,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'address': self.address,
        }
