from datetime import datetime
from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from . import db


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'user' | 'admin' | 'partner'

    # Relationships
    partner_profile = db.relationship('Partner', back_populates='user', uselist=False)
    orders = db.relationship('Order', back_populates='user')

    def __repr__(self):
        return f'<User {self.username}>'

    # Password reset token helpers
    def get_reset_token(self) -> str:
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token: str, max_age: int = 3600):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=max_age)
        except (BadSignature, SignatureExpired):
            return None
        return User.query.get(data.get('user_id'))


class Partner(db.Model):
    __tablename__ = 'partner'
    id = db.Column(db.Integer, primary_key=True)
    platform_name = db.Column(db.String(120), nullable=False)
    contact_email = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='partner_profile')
    time_slots = db.relationship('TimeSlot', back_populates='partner', cascade='all, delete-orphan')
    orders = db.relationship('Order', back_populates='partner')

    def __repr__(self):
        return f'<Partner {self.platform_name}>'


class TimeSlot(db.Model):
    __tablename__ = 'time_slot'
    id = db.Column(db.Integer, primary_key=True)
    partner_id = db.Column(db.Integer, db.ForeignKey('partner.id'), nullable=False)
    day_of_week = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.String(20), nullable=False)
    end_time = db.Column(db.String(20), nullable=False)
    max_capacity = db.Column(db.Integer, nullable=False, default=0)

    # Relationships
    partner = db.relationship('Partner', back_populates='time_slots')
    orders = db.relationship('Order', back_populates='time_slot')

    def __repr__(self):
        return f'<TimeSlot {self.day_of_week} {self.start_time}-{self.end_time} (cap={self.max_capacity})>'


class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    partner_id = db.Column(db.Integer, db.ForeignKey('partner.id'), nullable=False)
    time_slot_id = db.Column(db.Integer, db.ForeignKey('time_slot.id'), nullable=False)
    order_platform = db.Column(db.String(120), nullable=False)
    order_id_text = db.Column(db.String(120), nullable=False)
    college_reg_no = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    type = db.Column('type', db.String(20), nullable=False)  # 'Pickup' | 'Return'
    status = db.Column(db.String(20), nullable=False, default='Booked')  # 'Booked' | 'Completed' | 'Cancelled'
    booking_date = db.Column(db.Date, nullable=True)  # Date for which booking is made
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='orders')
    partner = db.relationship('Partner', back_populates='orders')
    time_slot = db.relationship('TimeSlot', back_populates='orders')

    def __repr__(self):
        return f'<Order {self.order_platform}:{self.order_id_text} {self.status}>'
