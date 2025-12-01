from mongoengine import Document, DateTimeField, ListField, EmbeddedDocument, EmbeddedDocumentField, StringField, ReferenceField, DictField
from datetime import datetime

class Registration(EmbeddedDocument):
    user_id = ReferenceField('User', required=True)
    guests = ListField(StringField())

    def to_dict(self):
        return {
            '_id': str(self.id) if hasattr(self, 'id') else None,
            'userId': self.user_id.to_dict() if self.user_id else None,
            'guests': self.guests or []
        }

class SlotDetails(EmbeddedDocument):
    teams = DictField()
    final_score = StringField(required=False)

    def to_dict(self):
        return {
            'teams': self.teams or {'teamA': [], 'teamB': []},
            'finalScore': self.final_score
        }

class Slot(Document):
    date = DateTimeField(required=True, unique=True)
    registrations = ListField(EmbeddedDocumentField(Registration))
    details = EmbeddedDocumentField(SlotDetails, default=SlotDetails)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'slots',
        'indexes': ['-date']
    }

    def get_total_participants(self):
        """Calculate total participants including guests"""
        count = len(self.registrations)
        for reg in self.registrations:
            count += len(reg.guests)
        return count

    def to_dict(self):
        """Convert to dictionary"""
        return {
            '_id': str(self.id),
            'id': str(self.id),
            'date': self.date.isoformat() if self.date else None,
            'registrations': [reg.to_dict() for reg in self.registrations] if self.registrations else [],
            'details': self.details.to_dict() if self.details else {'teams': {'teamA': [], 'teamB': []}, 'finalScore': None},
            'totalParticipants': self.get_total_participants(),
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }

    def save(self, *args, **kwargs):
        """Override save to update timestamp"""
        self.updated_at = datetime.utcnow()
        if not self.details:
            self.details = SlotDetails(teams={'teamA': [], 'teamB': []}, final_score=None)
        return super(Slot, self).save(*args, **kwargs)
