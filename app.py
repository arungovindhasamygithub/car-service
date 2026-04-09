from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import math
import csv
import io

db = SQLAlchemy()

# ==========================================
# DATABASE MODELS
# ==========================================

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    mobile = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    location = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Reward points for customers
    points = db.Column(db.Integer, default=0)
    
    # Franchise specific fields
    franchise_name = db.Column(db.String(100))
    franchise_address = db.Column(db.Text)
    franchise_location = db.Column(db.String(100))
    franchise_latitude = db.Column(db.Float)
    franchise_longitude = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    services = db.relationship('Service', foreign_keys='Service.customer_id', backref='customer')
    franchise_services = db.relationship('Service', foreign_keys='Service.franchise_id', backref='franchise')

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    brand_model = db.Column(db.String(100))
    reg_no = db.Column(db.String(50))
    year = db.Column(db.String(10))
    mileage = db.Column(db.String(50))
    fuel_type = db.Column(db.String(50))
    services = db.Column(db.Text) 
    specific_service_details = db.Column(db.Text)
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    alt_date = db.Column(db.String(20))
    alt_time = db.Column(db.String(20))
    service_location = db.Column(db.String(100))
    notes = db.Column(db.Text)
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EmergencyRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    emergency_contact = db.Column(db.String(50))
    brand_model = db.Column(db.String(100), nullable=False)
    reg_no = db.Column(db.String(50), nullable=False)
    fuel_type = db.Column(db.String(50))
    breakdown_nature = db.Column(db.Text)
    other_breakdown = db.Column(db.String(200))
    location = db.Column(db.Text, nullable=False)
    blocking_traffic = db.Column(db.String(10))
    assistance_required = db.Column(db.Text)
    payment_method = db.Column(db.String(50))
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FranchiseRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(20))
    gender = db.Column(db.String(20))
    nationality = db.Column(db.String(50))
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    residential_address = db.Column(db.Text)
    id_proof = db.Column(db.String(100))
    proposed_location = db.Column(db.String(100))
    current_occupation = db.Column(db.String(100))
    auto_experience = db.Column(db.String(100))
    franchise_experience = db.Column(db.String(100))
    capital = db.Column(db.String(50))
    funds_source = db.Column(db.String(50))
    franchise_model = db.Column(db.String(50))
    has_property = db.Column(db.String(50))
    timeline = db.Column(db.String(50))
    ownership = db.Column(db.String(50))
    property_size = db.Column(db.String(50))
    parking = db.Column(db.String(50))
    accessibility = db.Column(db.String(50))
    workforce = db.Column(db.String(100))
    reg_number = db.Column(db.String(100))
    gst_number = db.Column(db.String(100))
    legal_cases = db.Column(db.Text)
    reason = db.Column(db.Text)
    comments = db.Column(db.Text)
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    franchise_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)
    vehicle_model = db.Column(db.String(100))
    overall_status = db.Column(db.String(50), default='Pending')
    total_amount = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    service_items = db.relationship('ServiceItem', backref='service', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='service', cascade='all, delete-orphan')

class ServiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    issue_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='Pending')
    charge = db.Column(db.Float, default=0)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    franchise_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    issue = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    customer = db.relationship('User', foreign_keys=[customer_id])
    franchise = db.relationship('User', foreign_keys=[franchise_id])

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    franchise_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    price = db.Column(db.Float)
    description = db.Column(db.Text)
    franchise = db.relationship('User', foreign_keys=[franchise_id])

class PartsRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_franchise_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    to_franchise_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    from_franchise = db.relationship('User', foreign_keys=[from_franchise_id])
    to_franchise = db.relationship('User', foreign_keys=[to_franchise_id])

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Pending')
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ==========================================
# FLASK SETUP & CONFIGURATION
# ==========================================

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///car_service.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPI_ID'] = 'careservice@okhdfcbank'

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'customer_login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            role='admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371 
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# ==========================================
# PUBLIC ROUTES
# ==========================================

@app.route('/')
def index():
    branches = User.query.filter_by(role='franchise', is_active=True).all()
    return render_template('index.html', services=[], branches=branches)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html', services=[])

@app.route('/branches')
def branches():
    branches = User.query.filter_by(role='franchise', is_active=True).all()
    user_lat = request.args.get('lat', type=float)
    user_lng = request.args.get('lng', type=float)
    
    if user_lat and user_lng:
        for branch in branches:
            if branch.franchise_latitude and branch.franchise_longitude:
                branch.distance = calculate_distance(user_lat, user_lng, branch.franchise_latitude, branch.franchise_longitude)
            else:
                branch.distance = None
        branches = sorted(branches, key=lambda x: x.distance if x.distance else float('inf'))
    
    return render_template('branches.html', branches=branches)

@app.route('/franchise-request', methods=['POST'])
def franchise_request():
    if request.method == 'POST':
        franchise_req = FranchiseRequest(
            name=request.form.get('name'),
            dob=request.form.get('dob'),
            gender=request.form.get('gender'),
            nationality=request.form.get('nationality'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            residential_address=request.form.get('residential_address'),
            id_proof=request.form.get('id_proof'),
            proposed_location=request.form.get('proposed_location'),
            current_occupation=request.form.get('current_occupation'),
            auto_experience=request.form.get('auto_experience'),
            franchise_experience=request.form.get('franchise_experience'),
            capital=request.form.get('capital'),
            funds_source=request.form.get('funds_source'),
            franchise_model=request.form.get('franchise_model'),
            has_property=request.form.get('has_property'),
            timeline=request.form.get('timeline'),
            ownership=request.form.get('ownership'),
            property_size=request.form.get('property_size'),
            parking=request.form.get('parking'),
            accessibility=request.form.get('accessibility'),
            workforce=request.form.get('workforce'),
            reg_number=request.form.get('reg_number'),
            gst_number=request.form.get('gst_number'),
            legal_cases=request.form.get('legal_cases'),
            reason=request.form.get('reason'),
            comments=request.form.get('comments'),
            status='Pending'
        )
        db.session.add(franchise_req)
        db.session.commit()
        flash('Franchise request submitted successfully! Our team will review and contact you.', 'success')
        return redirect(url_for('index'))

@app.route('/book-appointment', methods=['POST'])
def book_appointment():
    services_list = request.form.getlist('services')
    services_str = ', '.join(services_list)

    appointment = Appointment(
        name=request.form.get('name'),
        phone=request.form.get('phone'),
        email=request.form.get('email'),
        address=request.form.get('address'),
        brand_model=request.form.get('brand_model'),
        reg_no=request.form.get('reg_no'),
        year=request.form.get('year'),
        mileage=request.form.get('mileage'),
        fuel_type=request.form.get('fuel_type'),
        services=services_str,
        specific_service_details=request.form.get('specific_service_details'),
        date=request.form.get('date'),
        time=request.form.get('time'),
        alt_date=request.form.get('alt_date'),
        alt_time=request.form.get('alt_time'),
        service_location=request.form.get('service_location'),
        notes=request.form.get('notes')
    )
    
    db.session.add(appointment)
    db.session.commit()
    
    flash('Appointment booked successfully! We will contact you shortly to confirm.', 'success')
    return redirect(url_for('index') + '#contact')

@app.route('/emergency-request', methods=['POST'])
def emergency_request():
    breakdown_list = request.form.getlist('breakdown_nature')
    assistance_list = request.form.getlist('assistance_required')

    emergency = EmergencyRequest(
        name=request.form.get('name'),
        phone=request.form.get('phone'),
        emergency_contact=request.form.get('emergency_contact'),
        brand_model=request.form.get('brand_model'),
        reg_no=request.form.get('reg_no'),
        fuel_type=request.form.get('fuel_type'),
        breakdown_nature=', '.join(breakdown_list),
        other_breakdown=request.form.get('other_breakdown'),
        location=request.form.get('location'),
        blocking_traffic=request.form.get('blocking_traffic'),
        assistance_required=', '.join(assistance_list),
        payment_method=request.form.get('payment_method')
    )
    db.session.add(emergency)
    db.session.commit()
    
    flash('EMERGENCY REQUEST RECEIVED! A technician is being dispatched immediately.', 'danger')
    return redirect(url_for('index'))

# ==========================================
# AUTHENTICATION ROUTES
# ==========================================

@app.route('/customer-login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        mobile = request.form.get('mobile')
        location = request.form.get('location')
        lat = request.form.get('lat', type=float)
        lng = request.form.get('lng', type=float)
        
        user = User.query.filter_by(mobile=mobile, role='customer').first()
        
        if user:
            if location:
                user.location = location
            if lat and lng:
                user.latitude = lat
                user.longitude = lng
            db.session.commit()
            login_user(user)
            return redirect(url_for('customer_dashboard'))
        else:
            flash('This mobile number is not registered. Please contact a service center.', 'danger')
            return redirect(url_for('customer_login'))
            
    return render_template('auth/customer_login.html')

@app.route('/franchise-login', methods=['GET', 'POST'])
def franchise_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username, role='franchise').first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('franchise_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('auth/franchise_login.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username, role='admin').first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('auth/admin_login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ==========================================
# CUSTOMER ROUTES
# ==========================================

@app.route('/customer/dashboard')
@login_required
def customer_dashboard():
    if current_user.role != 'customer':
        return redirect(url_for('index'))
    services = Service.query.filter_by(customer_id=current_user.id).order_by(Service.created_at.desc()).all()
    branches = User.query.filter_by(role='franchise', is_active=True).all()
    if current_user.latitude and current_user.longitude:
        for branch in branches:
            if branch.franchise_latitude and branch.franchise_longitude:
                branch.distance = calculate_distance(current_user.latitude, current_user.longitude, 
                                                   branch.franchise_latitude, branch.franchise_longitude)
        branches = sorted(branches, key=lambda x: x.distance if x.distance else float('inf'))[:3]
    return render_template('customer/dashboard.html', services=services, branches=branches)

@app.route('/customer/service-history')
@login_required
def service_history():
    if current_user.role != 'customer':
        return redirect(url_for('index'))
    services = Service.query.filter_by(customer_id=current_user.id).order_by(Service.created_at.desc()).all()
    return render_template('customer/service_history.html', services=services)

@app.route('/customer/track-service/<int:service_id>')
@login_required
def track_service(service_id):
    service = Service.query.get_or_404(service_id)
    if service.customer_id != current_user.id:
        return redirect(url_for('customer_dashboard'))
    return render_template('customer/track_service.html', service=service)

@app.route('/customer/payment/<int:service_id>', methods=['GET', 'POST'])
@login_required
def payment(service_id):
    service = Service.query.get_or_404(service_id)
    if request.method == 'POST':
        transaction_id = request.form.get('transaction_id')
        payment_record = Payment(
            service_id=service_id,
            amount=service.total_amount,
            status='Completed',
            payment_method='UPI',
            transaction_id=transaction_id
        )
        db.session.add(payment_record)
        points_earned = int(service.total_amount // 100)
        if hasattr(service.customer, 'points'):
             service.customer.points += points_earned
        db.session.commit()
        flash(f'Payment successful! You earned {points_earned} reward points.', 'success')
        return redirect(url_for('customer_dashboard'))
    payment_record = Payment.query.filter_by(service_id=service_id).first()
    return render_template('customer/payment.html', service=service, payment=payment_record, upi_id=app.config['UPI_ID'])

# ==========================================
# FRANCHISE ROUTES
# ==========================================

@app.route('/franchise/dashboard')
@login_required
def franchise_dashboard():
    if current_user.role != 'franchise':
        return redirect(url_for('index'))
    complaints = Complaint.query.filter_by(franchise_id=current_user.id).order_by(Complaint.created_at.desc()).limit(10).all()
    services = Service.query.filter_by(franchise_id=current_user.id).order_by(Service.created_at.desc()).all()
    return render_template('franchise/dashboard.html', complaints=complaints, services=services)

@app.route('/franchise/create-service', methods=['GET', 'POST'])
@login_required
def create_service():
    if current_user.role != 'franchise':
        return redirect(url_for('index'))
    if request.method == 'POST':
        mobile = request.form.get('mobile')
        location = request.form.get('location')
        vehicle_number = request.form.get('vehicle_number')
        vehicle_model = request.form.get('vehicle_model')
        customer = User.query.filter_by(mobile=mobile, role='customer').first()
        if not customer:
            customer = User(
                username=mobile, password=generate_password_hash(mobile),
                role='customer', mobile=mobile, location=location, is_active=True
            )
            db.session.add(customer)
            db.session.commit()
        elif location and not customer.location:
            customer.location = location
            db.session.commit()
        service = Service(
            customer_id=customer.id, franchise_id=current_user.id,
            vehicle_number=vehicle_number, vehicle_model=vehicle_model,
            overall_status='Pending', total_amount=0
        )
        db.session.add(service)
        db.session.commit()
        return redirect(url_for('add_service_items', service_id=service.id))
    return render_template('franchise/create_service.html')

@app.route('/franchise/add-service-items/<int:service_id>', methods=['GET', 'POST'])
@login_required
def add_service_items(service_id):
    service = Service.query.get_or_404(service_id)
    if service.franchise_id != current_user.id:
        return redirect(url_for('franchise_dashboard'))
    if request.method == 'POST':
        issue_types = request.form.getlist('issue_type[]')
        descriptions = request.form.getlist('description[]')
        charges = request.form.getlist('charge[]')
        total = 0
        for i in range(len(issue_types)):
            if issue_types[i]:
                item = ServiceItem(
                    service_id=service_id, issue_type=issue_types[i],
                    description=descriptions[i] if i < len(descriptions) else '',
                    status='Pending', charge=float(charges[i]) if i < len(charges) and charges[i] else 0
                )
                db.session.add(item)
                total += float(charges[i]) if i < len(charges) and charges[i] else 0
        service.total_amount = total
        db.session.commit()
        flash('Service items added successfully!', 'success')
        return redirect(url_for('franchise_dashboard'))
    return render_template('franchise/add_service_items.html', service=service, issues_list=[])

@app.route('/franchise/update-item-status/<int:item_id>', methods=['POST'])
@login_required
def update_item_status(item_id):
    item = ServiceItem.query.get_or_404(item_id)
    service = Service.query.get(item.service_id)
    if service.franchise_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    new_status = request.json.get('status')
    item.status = new_status
    if new_status == 'In Progress' and not item.started_at:
        item.started_at = datetime.utcnow()
    elif new_status == 'Completed' and not item.completed_at:
        item.completed_at = datetime.utcnow()
    all_items = ServiceItem.query.filter_by(service_id=item.service_id).all()
    all_completed = all(i.status == 'Completed' for i in all_items)
    if all_completed:
        service.overall_status = 'Completed'
        service.completed_at = datetime.utcnow()
    elif any(i.status == 'In Progress' for i in all_items):
        service.overall_status = 'In Progress'
    else:
        service.overall_status = 'Pending'
    db.session.commit()
    return jsonify({'success': True, 'overall_status': service.overall_status})

@app.route('/franchise/complaints', methods=['GET', 'POST'])
@login_required
def complaints():
    if current_user.role != 'franchise':
        return redirect(url_for('index'))
    if request.method == 'POST':
        mobile = request.form.get('mobile')
        issue = request.form.get('issue')
        customer = User.query.filter_by(mobile=mobile, role='customer').first()
        if not customer:
            customer = User(
                username=mobile, password=generate_password_hash(mobile),
                role='customer', mobile=mobile, is_active=True
            )
            db.session.add(customer)
            db.session.commit()
        complaint = Complaint(
            customer_id=customer.id, franchise_id=current_user.id,
            issue=issue, status='Pending'
        )
        db.session.add(complaint)
        db.session.commit()
        flash('Complaint registered successfully!', 'success')
        return redirect(url_for('complaints'))
    complaints_list = Complaint.query.filter_by(franchise_id=current_user.id).all()
    return render_template('franchise/complaints.html', complaints=complaints_list)

@app.route('/franchise/inventory', methods=['GET', 'POST'])
@login_required
def inventory():
    if current_user.role != 'franchise':
        return redirect(url_for('index'))
    if request.method == 'POST':
        product = Product(
            franchise_id=current_user.id, name=request.form.get('product_name'),
            quantity=int(request.form.get('quantity')), price=float(request.form.get('price')),
            description=request.form.get('description')
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('inventory'))
    products = Product.query.filter_by(franchise_id=current_user.id).all()
    return render_template('franchise/inventory.html', products=products)

@app.route('/franchise/update-product/<int:product_id>', methods=['POST'])
@login_required
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.franchise_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    product.quantity = data.get('quantity', product.quantity)
    product.price = data.get('price', product.price)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/franchise/update-complaint-status/<int:complaint_id>', methods=['POST'])
@login_required
def update_complaint_status(complaint_id):
    if current_user.role != 'franchise':
        return jsonify({'error': 'Unauthorized'}), 403
    complaint = Complaint.query.get_or_404(complaint_id)
    if complaint.franchise_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    new_status = data.get('status')
    if new_status in ['Pending', 'Processing', 'Hold', 'Completed']:
        complaint.status = new_status
        db.session.commit()
        return jsonify({'success': True, 'status': new_status})
    return jsonify({'error': 'Invalid status'}), 400

@app.route('/franchise/parts-request', methods=['GET', 'POST'])
@login_required
def parts_request():
    if current_user.role != 'franchise':
        return redirect(url_for('index'))
    if request.method == 'POST':
        req = PartsRequest(
            from_franchise_id=current_user.id, product_name=request.form.get('product_name'),
            quantity=int(request.form.get('quantity')), status='Pending'
        )
        db.session.add(req)
        db.session.commit()
        flash('Parts request submitted!', 'success')
        return redirect(url_for('parts_request'))
    requests_list = PartsRequest.query.filter_by(from_franchise_id=current_user.id).all()
    available_requests = PartsRequest.query.filter(
        PartsRequest.status == 'Pending', PartsRequest.from_franchise_id != current_user.id
    ).all()
    return render_template('franchise/parts_request.html', requests=requests_list, available_requests=available_requests)

@app.route('/franchise/fulfill-request/<int:request_id>', methods=['POST'])
@login_required
def fulfill_request(request_id):
    req = PartsRequest.query.get_or_404(request_id)
    req.to_franchise_id = current_user.id
    req.status = 'Approved'
    db.session.commit()
    flash('Request fulfilled!', 'success')
    return redirect(url_for('parts_request'))

# ==========================================
# ADMIN ROUTES
# ==========================================

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    total_customers = User.query.filter_by(role='customer').count()
    total_franchises = User.query.filter_by(role='franchise').count()
    total_services = Service.query.count()
    total_complaints = Complaint.query.count()
    pending_requests = FranchiseRequest.query.filter_by(status='Pending').count()
    return render_template('admin/dashboard.html', 
                         total_customers=total_customers, total_franchises=total_franchises,
                         total_services=total_services, total_complaints=total_complaints,
                         pending_requests=pending_requests)

@app.route('/admin/emergency-requests')
@login_required
def manage_emergencies():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    emergencies = EmergencyRequest.query.order_by(EmergencyRequest.created_at.desc()).all()
    return render_template('admin/emergency_requests.html', emergencies=emergencies)

@app.route('/admin/update-emergency-status/<int:req_id>', methods=['POST'])
@login_required
def update_emergency_status(req_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    emergency = EmergencyRequest.query.get_or_404(req_id)
    data = request.get_json()
    new_status = data.get('status')
    if new_status:
        emergency.status = new_status
        db.session.commit()
        return jsonify({'success': True, 'status': new_status})
    return jsonify({'error': 'Invalid status'}), 400

@app.route('/admin/appointments')
@login_required
def manage_appointments():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    appointments = Appointment.query.order_by(Appointment.created_at.desc()).all()
    return render_template('admin/appointments.html', appointments=appointments)

@app.route('/admin/manage-customers')
@login_required
def manage_customers():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    customers = User.query.filter_by(role='customer').order_by(User.id.desc()).all()
    return render_template('admin/manage_customers.html', customers=customers)

@app.route('/admin/add-customer', methods=['POST'])
@login_required
def add_customer():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    mobile = request.form.get('mobile')
    email = request.form.get('email')
    location = request.form.get('location')
    if not User.query.filter_by(mobile=mobile, role='customer').first():
        user = User(
            username=mobile, password=generate_password_hash(mobile),
            role='customer', mobile=mobile, email=email,
            location=location, is_active=True
        )
        db.session.add(user)
        db.session.commit()
        flash('Customer added successfully!', 'success')
    else:
        flash('A customer with this mobile number already exists.', 'danger')
    return redirect(url_for('manage_customers'))

@app.route('/admin/import-customers', methods=['POST'])
@login_required
def import_customers():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    if 'file' not in request.files:
        flash('No file uploaded.', 'danger')
        return redirect(url_for('manage_customers'))
    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('manage_customers'))
    if file and file.filename.endswith('.csv'):
        try:
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_input = csv.DictReader(stream)
            count = 0
            for row in csv_input:
                mobile = row.get('mobile')
                if mobile and not User.query.filter_by(mobile=mobile, role='customer').first():
                    user = User(
                        username=mobile, password=generate_password_hash(mobile),
                        role='customer', mobile=mobile, email=row.get('email', ''),
                        location=row.get('location', ''), is_active=True
                    )
                    db.session.add(user)
                    count += 1
            db.session.commit()
            flash(f'Successfully imported {count} customers from CSV.', 'success')
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'danger')
    else:
        flash('Invalid file format. Please upload a valid CSV file.', 'danger')
    return redirect(url_for('manage_customers'))

@app.route('/admin/toggle-customer-status/<int:customer_id>', methods=['POST'])
@login_required
def toggle_customer_status(customer_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    customer = User.query.get_or_404(customer_id)
    customer.is_active = not customer.is_active
    db.session.commit()
    return jsonify({'success': True, 'is_active': customer.is_active})

@app.route('/admin/manage-franchises', methods=['GET', 'POST'])
@login_required
def manage_franchises():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            mobile = request.form.get('mobile')
            existing_user = User.query.filter_by(username=mobile, role='franchise').first()
            if existing_user:
                flash('A franchise with this Login ID (Mobile) already exists.', 'danger')
                return redirect(url_for('manage_franchises'))

            franchise = User(
                username=mobile, 
                password=generate_password_hash(request.form.get('password')),
                role='franchise',
                mobile=mobile,
                email=request.form.get('email'),
                franchise_name=request.form.get('franchise_name'), 
                franchise_location=request.form.get('location'),   
                franchise_address=request.form.get('address'),     
                is_active=True
            )
            db.session.add(franchise)
            db.session.commit()
            flash('Franchise created successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while creating the franchise: {str(e)}', 'danger')
            
        return redirect(url_for('manage_franchises'))
    
    franchises = User.query.filter_by(role='franchise').all()
    return render_template('admin/manage_franchises.html', franchises=franchises)

@app.route('/admin/reset-franchise-password/<int:franchise_id>', methods=['POST'])
@login_required
def reset_franchise_password(franchise_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    franchise = User.query.get_or_404(franchise_id)
    data = request.get_json()
    new_password = data.get('password')
    if not new_password:
        return jsonify({'error': 'Password cannot be empty'}), 400
    franchise.password = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/delete-franchise/<int:franchise_id>', methods=['POST'])
@login_required
def delete_franchise(franchise_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    franchise = User.query.get_or_404(franchise_id)
    db.session.delete(franchise)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/approve-requests')
@login_required
def approve_requests():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    requests_list = FranchiseRequest.query.filter_by(status='Pending').all()
    return render_template('admin/approve_requests.html', requests=requests_list)

@app.route('/admin/approve-franchise/<int:request_id>', methods=['POST'])
@login_required
def approve_franchise(request_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    req = FranchiseRequest.query.get_or_404(request_id)
    req.status = 'Approved'
    franchise = User(
        username=req.phone, 
        password=generate_password_hash(req.phone),
        role='franchise',
        franchise_name=req.name,
        franchise_address=req.residential_address,
        franchise_location=req.proposed_location,
        is_active=True
    )
    db.session.add(franchise)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/reject-franchise/<int:request_id>', methods=['POST'])
@login_required
def reject_franchise(request_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    req = FranchiseRequest.query.get_or_404(request_id)
    req.status = 'Rejected'
    db.session.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)