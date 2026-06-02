from datetime import datetime
import uuid
from . import db, GUID


class ProjectPhoto(db.Model):
    __tablename__ = 'project_photos'

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(GUID(), db.ForeignKey('projects.id'), nullable=False)

    activity_date = db.Column(db.Date)
    activity_description = db.Column(db.Text)
    photo_url = db.Column(db.String(500))
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'activity_date': self.activity_date.isoformat() if self.activity_date else None,
            'activity_description': self.activity_description,
            'photo_url': self.photo_url,
            'notes': self.notes,
        }
