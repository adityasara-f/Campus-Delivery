# Deployment Instructions for Render

## Important: Run These Commands After Deployment

After deploying to Render, you need to run these commands in the Render Shell:

### 1. Add the booking_date column (one-time migration)
```bash
python migrate_booking_date.py
```

### 2. Seed the database with partners and slots
```bash
python -c "import sys; sys.path.insert(0, '.'); exec(open('scripts/seed.py').read())"
```

Or alternatively:
```bash
cd scripts && python seed.py
```

## Access the Render Shell

1. Go to your service on Render dashboard
2. Click on "Shell" tab
3. Run the commands above

## Default Credentials

After seeding, you can log in with:

### Admin
- Username: `admin`
- Password: `Admin@123`

### Partners
- Amazon: `amazon` / `Amazon@123`
- Flipkart: `flipkart` / `Flipkart@123`

## Database Schema Changes

If you update the models in the future, you may need to:
1. Create a new migration script similar to `migrate_booking_date.py`
2. Run it in the Render shell after deployment
