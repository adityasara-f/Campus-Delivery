from app import create_app, db
from app.models import Order
from datetime import datetime

app = create_app()

with app.app_context():
    # Update all orders without a booking_date to use today's date
    orders_without_date = Order.query.filter_by(booking_date=None).all()
    
    if orders_without_date:
        for order in orders_without_date:
            order.booking_date = datetime.now().date()
        db.session.commit()
        print(f'✓ Updated {len(orders_without_date)} orders with booking_date')
    else:
        print('✓ All orders already have booking_date set')
