from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, abort
from flask_login import login_required, current_user, login_user, logout_user
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash
from . import login_manager, db, mail
from .models import User, Partner, TimeSlot, Order
from .forms import RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm, ChangePasswordForm
from datetime import datetime

bp = Blueprint('main', __name__)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -------------------- Authentication --------------------
@bp.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('home.html')


@bp.route('/signin', methods=['GET', 'POST'])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        ident = form.email.data.strip()
        user = User.query.filter_by(email=ident.lower()).first()
        if not user:
            user = User.query.filter_by(username=ident).first()
        if not user or not check_password_hash(user.password_hash, form.password.data):
            flash('Invalid email/username or password', 'warning')
            return render_template('signin.html', form=form)
        login_user(user, remember=form.remember.data)
        return redirect(url_for('main.dashboard'))
    return render_template('signin.html', form=form)


# Keep old /login route for backwards compatibility
@bp.route('/login', methods=['GET', 'POST'])
def login():
    return redirect(url_for('main.signin'))


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.lower(),
            password_hash=generate_password_hash(form.password.data),
            role=form.role.data,
        )
        db.session.add(user)
        db.session.flush()
        if user.role == 'partner':
            partner = Partner(platform_name=form.username.data.strip(), contact_email=form.email.data.lower(), user_id=user.id)
            db.session.add(partner)
        db.session.commit()
        flash('Account created. Please sign in.', 'success')
        return redirect(url_for('main.signin'))
    return render_template('signup.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))


# Password change (replaces forgot password)
@bp.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if not user:
            flash('Invalid username, email, or password', 'warning')
            return render_template('change_password.html', form=form)
        if user.email.lower() != form.email.data.lower():
            flash('Invalid username, email, or password', 'warning')
            return render_template('change_password.html', form=form)
        if not check_password_hash(user.password_hash, form.old_password.data):
            flash('Invalid username, email, or password', 'warning')
            return render_template('change_password.html', form=form)
        user.password_hash = generate_password_hash(form.new_password.data)
        db.session.commit()
        flash('Your password has been updated! You can now sign in.', 'success')
        return redirect(url_for('main.signin'))
    return render_template('change_password.html', form=form)




# -------------------- Main / User --------------------
@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('main.admin_dashboard'))
    if current_user.role == 'partner':
        return redirect(url_for('main.partner_dashboard'))
    return redirect(url_for('main.user_dashboard'))


@bp.route('/user_dashboard')
@login_required
def user_dashboard():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('dashboard_user.html', orders=orders)








# -------------------- Partner --------------------
@bp.route('/partner_dashboard', methods=['GET', 'POST'])
@login_required
def partner_dashboard():
    if current_user.role != 'partner':
        abort(403)
    partner = Partner.query.filter_by(user_id=current_user.id).first()
    if not partner:
        flash('Partner profile not found', 'warning')
        return render_template('dashboard_partner.html', partner=None, orders=[], slots=[])

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create_slot':
            day_of_week = request.form.get('day_of_week')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            max_capacity = request.form.get('max_capacity', type=int)
            if not all([day_of_week, start_time, end_time]) or max_capacity is None:
                flash('All slot fields are required', 'warning')
            else:
                slot = TimeSlot(
                    partner_id=partner.id,
                    day_of_week=day_of_week,
                    start_time=start_time,
                    end_time=end_time,
                    max_capacity=max_capacity,
                )
                db.session.add(slot)
                db.session.commit()
                flash('Time slot created', 'success')
        elif action == 'delete_slot':
            slot_id = request.form.get('slot_id', type=int)
            slot = TimeSlot.query.filter_by(id=slot_id, partner_id=partner.id).first()
            if not slot:
                flash('Slot not found', 'warning')
            else:
                has_orders = Order.query.filter_by(time_slot_id=slot.id).first() is not None
                if has_orders:
                    flash('Cannot delete slot with existing orders', 'warning')
                else:
                    db.session.delete(slot)
                    db.session.commit()
                    flash('Time slot deleted', 'success')

    orders = Order.query.filter_by(partner_id=partner.id).order_by(Order.created_at.desc()).all()
    slots = TimeSlot.query.filter_by(partner_id=partner.id).all()
    return render_template('dashboard_partner.html', partner=partner, orders=orders, slots=slots)




# -------------------- Admin --------------------
@bp.route('/admin_dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        abort(403)

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create_partner':
            platform_name = request.form.get('platform_name')
            contact_email = request.form.get('contact_email')
            username = request.form.get('username')
            password = request.form.get('password')
            if not all([platform_name, username, password]):
                flash('Platform name, username, and password are required', 'warning')
            elif User.query.filter_by(username=username).first():
                flash('Username already exists', 'warning')
            else:
                user = User(username=username, password_hash=generate_password_hash(password), role='partner')
                db.session.add(user)
                db.session.flush()  # get user.id
                partner = Partner(platform_name=platform_name, contact_email=contact_email, user_id=user.id)
                db.session.add(partner)
                db.session.commit()
                flash('Partner account created', 'success')
        elif action == 'delete_user':
            user_id = request.form.get('user_id', type=int)
            user = User.query.get(user_id)
            if not user:
                flash('User not found', 'warning')
            else:
                # If partner, delete partner profile first
                if user.role == 'partner' and user.partner_profile:
                    # Deleting partner will cascade delete time slots
                    db.session.delete(user.partner_profile)
                db.session.delete(user)
                db.session.commit()
                flash('User deleted', 'success')
        elif action == 'set_role':
            user_id = request.form.get('user_id', type=int)
            role = request.form.get('role')
            if role not in ('user', 'admin', 'partner'):
                flash('Invalid role', 'warning')
            else:
                user = User.query.get(user_id)
                if not user:
                    flash('User not found', 'warning')
                else:
                    user.role = role
                    db.session.commit()
                    flash('Role updated', 'success')

    users = User.query.order_by(User.id.asc()).all()
    partners = Partner.query.order_by(Partner.platform_name.asc()).all()
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('dashboard_admin.html', users=users, partners=partners, orders=orders)




# -------------------- API ROUTES --------------------
@bp.route('/api/get_slots/<int:partner_id>')
@login_required
def api_get_slots_by_id(partner_id):
    partner = Partner.query.get_or_404(partner_id)
    
    # Get selected date from query parameter, default to today
    date_str = request.args.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = datetime.now().date()
    else:
        selected_date = datetime.now().date()
    
    day_of_week = selected_date.strftime('%A')
    slots = TimeSlot.query.filter_by(partner_id=partner.id, day_of_week=day_of_week).all()

    available_slots = []
    for slot in slots:
        # Count bookings for this specific slot on this specific date
        booked_count = Order.query.filter_by(
            time_slot_id=slot.id,
            booking_date=selected_date
        ).count()
        if booked_count < slot.max_capacity:
            available_slots.append({
                'id': slot.id,
                'start_time': slot.start_time,
                'end_time': slot.end_time,
                'available_capacity': slot.max_capacity - booked_count,
            })
    return jsonify(available_slots)


# New unified New Order route (GET + POST)
@bp.route('/order/new', methods=['GET', 'POST'])
@login_required
def order_new():
    if request.method == 'POST':
        partner_id = request.form.get('partner_id')
        time_slot_id = request.form.get('time_slot_id')
        booking_date_str = request.form.get('booking_date')
        order_platform = None  # optional; could infer from partner
        order_id_text = request.form.get('order_id_text')
        college_reg_no = request.form.get('college_reg_no')
        name = request.form.get('name')
        phone = request.form.get('phone')
        type_ = request.form.get('type')
        
        # Parse booking date
        try:
            booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date() if booking_date_str else datetime.now().date()
        except ValueError:
            booking_date = datetime.now().date()

        # Resolve partner
        partner = Partner.query.get(int(partner_id)) if partner_id else None
        if not partner:
            flash('Partner not found', 'warning')
            return redirect(url_for('main.order_new'))

        # Validate time slot
        if not time_slot_id:
            flash('Please select a time slot', 'warning')
            return redirect(url_for('main.order_new'))
        slot = TimeSlot.query.get(int(time_slot_id))
        if not slot or slot.partner_id != partner.id:
            flash('Invalid time slot selection', 'warning')
            return redirect(url_for('main.order_new'))

        # Capacity check for specific date
        current_count = Order.query.filter_by(
            time_slot_id=slot.id,
            booking_date=booking_date
        ).count()
        if current_count >= slot.max_capacity:
            flash('Selected time slot is full for that date', 'warning')
            return redirect(url_for('main.order_new'))

        # Basic validation
        required = [order_id_text, college_reg_no, name, phone, type_]
        if any(not v for v in required):
            flash('All fields are required', 'warning')
            return redirect(url_for('main.order_new'))

        order = Order(
            user_id=current_user.id,
            partner_id=partner.id,
            time_slot_id=slot.id,
            order_platform=partner.platform_name,
            order_id_text=order_id_text,
            college_reg_no=college_reg_no,
            name=name,
            phone=phone,
            type=type_,
            status='Booked',
            booking_date=booking_date,
        )
        db.session.add(order)
        db.session.commit()
        flash('Order booked successfully', 'success')
        return redirect(url_for('main.user_dashboard'))

    partners = Partner.query.order_by(Partner.platform_name.asc()).all()
    return render_template('new_order.html', title='New Order', partners=partners)
