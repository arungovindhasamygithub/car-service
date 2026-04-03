from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Service, ServiceItem, Complaint, Product, PartsRequest, Payment, FranchiseRequest
from datetime import datetime
import json
import math
import csv
import io

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

@app.route('/')
def index():
    branches = User.query.filter_by(role='franchise', is_active=True).all()
    return render_template('index.html', services=[], branches=branches)

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

@app.route('/franchise-request', methods=['GET', 'POST'])
def franchise_request():
    if request.method == 'POST':
        franchise_req = FranchiseRequest(
            name=request.form.get('name'),
            email=request.form.get('email'),
            mobile=request.form.get('mobile'),
            location=request.form.get('location'),
            address=request.form.get('address'),
            investment=request.form.get('investment'),
            experience=request.form.get('experience'),
            reason=request.form.get('reason'),
            status='Pending'
        )
        db.session.add(franchise_req)
        db.session.commit()
        flash('Franchise request submitted successfully! Admin will review it.', 'success')
        return redirect(url_for('index'))
    return render_template('franchise_request.html')



@app.route('/customer-login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        mobile = request.form.get('mobile')
        location = request.form.get('location')
        lat = request.form.get('lat', type=float)
        lng = request.form.get('lng', type=float)
        
        user = User.query.filter_by(mobile=mobile, role='customer').first()
        
        if user:
            # If the user exists, update their location context for this session
            if location:
                user.location = location
            if lat and lng:
                user.latitude = lat
                user.longitude = lng
            
            db.session.commit()
            login_user(user)
            return redirect(url_for('customer_dashboard'))
        else:
            flash('This mobile number is not registered. Please contact a service center to register.', 'danger')
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
        db.session.commit()
        flash('Payment successful!', 'success')
        return redirect(url_for('customer_dashboard'))
    
    payment_record = Payment.query.filter_by(service_id=service_id).first()
    return render_template('customer/payment.html', service=service, payment=payment_record, upi_id=app.config['UPI_ID'])

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
                username=mobile,
                password=generate_password_hash(mobile),
                role='customer',
                mobile=mobile,
                location=location,
                is_active=True
            )
            db.session.add(customer)
            db.session.commit()
        elif location and not customer.location:
            customer.location = location
            db.session.commit()
        
        service = Service(
            customer_id=customer.id,
            franchise_id=current_user.id,
            vehicle_number=vehicle_number,
            vehicle_model=vehicle_model,
            overall_status='Pending',
            total_amount=0
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
                    service_id=service_id,
                    issue_type=issue_types[i],
                    description=descriptions[i] if i < len(descriptions) else '',
                    status='Pending',
                    charge=float(charges[i]) if i < len(charges) and charges[i] else 0
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
                username=mobile,
                password=generate_password_hash(mobile),
                role='customer',
                mobile=mobile,
                is_active=True
            )
            db.session.add(customer)
            db.session.commit()
        
        complaint = Complaint(
            customer_id=customer.id,
            franchise_id=current_user.id,
            issue=issue,
            status='Pending'
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
            franchise_id=current_user.id,
            name=request.form.get('product_name'),
            quantity=int(request.form.get('quantity')),
            price=float(request.form.get('price')),
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
            from_franchise_id=current_user.id,
            product_name=request.form.get('product_name'),
            quantity=int(request.form.get('quantity')),
            status='Pending'
        )
        db.session.add(req)
        db.session.commit()
        flash('Parts request submitted!', 'success')
        return redirect(url_for('parts_request'))
    
    requests_list = PartsRequest.query.filter_by(from_franchise_id=current_user.id).all()
    available_requests = PartsRequest.query.filter(
        PartsRequest.status == 'Pending', 
        PartsRequest.from_franchise_id != current_user.id
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
                         total_customers=total_customers,
                         total_franchises=total_franchises,
                         total_services=total_services,
                         total_complaints=total_complaints,
                         pending_requests=pending_requests)

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
            username=mobile,
            password=generate_password_hash(mobile),
            role='customer',
            mobile=mobile,
            email=email,
            location=location,
            is_active=True
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
                        username=mobile,
                        password=generate_password_hash(mobile),
                        role='customer',
                        mobile=mobile,
                        email=row.get('email', ''),
                        location=row.get('location', ''),
                        is_active=True
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
        franchise = User(
            username=request.form.get('username'),
            password=generate_password_hash(request.form.get('password')),
            role='franchise',
            franchise_name=request.form.get('franchise_name'),
            franchise_address=request.form.get('address'),
            franchise_location=request.form.get('location'),
            franchise_latitude=request.form.get('latitude', type=float),
            franchise_longitude=request.form.get('longitude', type=float),
            is_active=True
        )
        db.session.add(franchise)
        db.session.commit()
        flash('Franchise created successfully!', 'success')
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
        username=req.mobile,
        password=generate_password_hash(req.mobile),
        role='franchise',
        franchise_name=req.name,
        franchise_address=req.address,
        franchise_location=req.location,
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


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)