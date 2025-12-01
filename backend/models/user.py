from mongoengine import Document, StringField, EmailField, DateTimeField, BooleanField, ReferenceField
from datetime import datetime
import bcrypt

class User(Document):
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    display_name = StringField(required=True, unique=True)
    email = EmailField(required=True, unique=True)
    password = StringField(required=True, min_length=6)
    registration_date = DateTimeField(default=datetime.utcnow)
    sponsored_by = ReferenceField('self', required=False)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'users',
        'indexes': ['email', 'display_name']
    }

    def set_password(self, password):
        """Hash and set password"""
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        """Check if password matches"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    def to_dict(self, include_password=False):
        """Convert to dictionary, excluding password by default"""
        data = {
            'id': str(self.id),
            '_id': str(self.id),
            'firstName': self.first_name,
            'lastName': self.last_name,
            'displayName': self.display_name,
            'email': self.email,
            'registrationDate': self.registration_date.isoformat() if self.registration_date else None,
            'sponsoredBy': str(self.sponsored_by.id) if self.sponsored_by else None,
            'isActive': self.is_active,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_password:
            data['password'] = self.password
        return data

    def save(self, *args, **kwargs):
        """Override save to update timestamp"""
        self.updated_at = datetime.utcnow()
        return super(User, self).save(*args, **kwargs)
