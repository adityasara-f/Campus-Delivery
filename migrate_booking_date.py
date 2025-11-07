from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Try to add the column
        db.session.execute(text('ALTER TABLE "order" ADD COLUMN booking_date DATE'))
        db.session.commit()
        print('✓ Successfully added booking_date column to order table')
    except Exception as e:
        if 'duplicate column name' in str(e).lower() or 'already exists' in str(e).lower():
            print('✓ booking_date column already exists')
        else:
            print(f'Error: {e}')
            db.session.rollback()
