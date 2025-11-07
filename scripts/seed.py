from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import User, Partner, TimeSlot

app = create_app()

with app.app_context():
    db.create_all()

    def ensure_user(username, password, role):
        u = User.query.filter_by(username=username).first()
        if not u:
            u = User(username=username, password_hash=generate_password_hash(password), role=role)
            db.session.add(u)
            db.session.commit()
        return u

    admin = ensure_user('admin', 'admin123', 'admin')
    partner_user = ensure_user('amazon_manager', 'amazon123', 'partner')

    partner = Partner.query.filter_by(platform_name='Amazon').first()
    if not partner:
        partner = Partner(platform_name='Amazon', contact_email='manager@amazon.example', user_id=partner_user.id)
        db.session.add(partner)
        db.session.commit()

    if not TimeSlot.query.filter_by(partner_id=partner.id).first():
        db.session.add(TimeSlot(partner_id=partner.id, day_of_week='Monday', start_time='10:00 AM', end_time='11:00 AM', max_capacity=20))
        db.session.commit()

    print('Seeded: admin/admin123, amazon_manager/amazon123, partner Amazon with a slot.')
