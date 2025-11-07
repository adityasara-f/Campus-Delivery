from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import User, Partner, TimeSlot

app = create_app()

with app.app_context():
    db.create_all()

    def ensure_user(username, password, role, email=None):
        u = User.query.filter_by(username=username).first()
        if not u:
            u = User(
                username=username,
                email=email or f"{username}@example.com",
                password_hash=generate_password_hash(password),
                role=role
            )
            db.session.add(u)
            db.session.commit()
        return u

    # Create admin
    admin = ensure_user('admin', 'Admin@123', 'admin', 'admin@campus.edu')
    
    # Create Amazon partner
    amazon_user = ensure_user('amazon', 'Amazon@123', 'partner', 'amazon@delivery.com')
    amazon_partner = Partner.query.filter_by(platform_name='Amazon').first()
    if not amazon_partner:
        amazon_partner = Partner(
            platform_name='Amazon',
            contact_email='amazon@delivery.com',
            user_id=amazon_user.id
        )
        db.session.add(amazon_partner)
        db.session.commit()
    
    # Create Flipkart partner
    flipkart_user = ensure_user('flipkart', 'Flipkart@123', 'partner', 'flipkart@delivery.com')
    flipkart_partner = Partner.query.filter_by(platform_name='Flipkart').first()
    if not flipkart_partner:
        flipkart_partner = Partner(
            platform_name='Flipkart',
            contact_email='flipkart@delivery.com',
            user_id=flipkart_user.id
        )
        db.session.add(flipkart_partner)
        db.session.commit()
    
    # Define time slots
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Time slots: 9-11 AM (30-min intervals), 12-2 PM (30-min intervals), 3-4 PM (30-min intervals)
    time_slots = [
        ('9:00 AM', '9:30 AM'),
        ('9:30 AM', '10:00 AM'),
        ('10:00 AM', '10:30 AM'),
        ('10:30 AM', '11:00 AM'),
        ('12:00 PM', '12:30 PM'),
        ('12:30 PM', '1:00 PM'),
        ('1:00 PM', '1:30 PM'),
        ('1:30 PM', '2:00 PM'),
        ('3:00 PM', '3:30 PM'),
        ('3:30 PM', '4:00 PM'),
    ]
    
    # Add time slots for Amazon
    existing_amazon_slots = TimeSlot.query.filter_by(partner_id=amazon_partner.id).count()
    if existing_amazon_slots == 0:
        for day in days:
            for start, end in time_slots:
                slot = TimeSlot(
                    partner_id=amazon_partner.id,
                    day_of_week=day,
                    start_time=start,
                    end_time=end,
                    max_capacity=15
                )
                db.session.add(slot)
        db.session.commit()
        print(f'Added {len(days) * len(time_slots)} time slots for Amazon')
    
    # Add time slots for Flipkart
    existing_flipkart_slots = TimeSlot.query.filter_by(partner_id=flipkart_partner.id).count()
    if existing_flipkart_slots == 0:
        for day in days:
            for start, end in time_slots:
                slot = TimeSlot(
                    partner_id=flipkart_partner.id,
                    day_of_week=day,
                    start_time=start,
                    end_time=end,
                    max_capacity=15
                )
                db.session.add(slot)
        db.session.commit()
        print(f'Added {len(days) * len(time_slots)} time slots for Flipkart')
    
    print('\n=== SEEDING COMPLETE ===')
    print('\nPartner Credentials:')
    print('  Amazon  - Username: amazon   | Password: Amazon@123')
    print('  Flipkart - Username: flipkart | Password: Flipkart@123')
    print('\nAdmin Credentials:')
    print('  Username: admin | Password: Admin@123')
    print('\nTime Slots: All days (Mon-Sun), 9-11 AM, 12-2 PM, 3-4 PM (30-min intervals)')
