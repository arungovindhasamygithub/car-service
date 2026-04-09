from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

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
    
    # Section 1: Customer Info
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    
    # Section 2: Vehicle Details
    brand_model = db.Column(db.String(100))
    reg_no = db.Column(db.String(50))
    year = db.Column(db.String(10))
    mileage = db.Column(db.String(50))
    fuel_type = db.Column(db.String(50))
    
    # Section 3: Services
    services = db.Column(db.Text) 
    specific_service_details = db.Column(db.Text)
    
    # Section 4: Schedule
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    alt_date = db.Column(db.String(20))
    alt_time = db.Column(db.String(20))
    service_location = db.Column(db.String(100))
    
    # Section 5: Notes
    notes = db.Column(db.Text)
    
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class EmergencyRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Section 1: Customer Info
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    emergency_contact = db.Column(db.String(50))
    
    # Section 2: Vehicle Details
    brand_model = db.Column(db.String(100), nullable=False)
    reg_no = db.Column(db.String(50), nullable=False)
    fuel_type = db.Column(db.String(50))
    
    # Section 3: Breakdown Details
    breakdown_nature = db.Column(db.Text)
    other_breakdown = db.Column(db.String(200))
    location = db.Column(db.Text, nullable=False)
    blocking_traffic = db.Column(db.String(10))
    
    # Section 4 & 5: Assistance & Payment
    assistance_required = db.Column(db.Text)
    payment_method = db.Column(db.String(50))
    
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FranchiseRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Section 1: Applicant Details
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(20))
    gender = db.Column(db.String(20))
    nationality = db.Column(db.String(50))
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    residential_address = db.Column(db.Text)
    id_proof = db.Column(db.String(100))
    
    # Section 2: Business Information
    proposed_location = db.Column(db.String(100))
    current_occupation = db.Column(db.String(100))
    auto_experience = db.Column(db.String(100))
    franchise_experience = db.Column(db.String(100))
    
    # Section 3: Investment & Financials
    capital = db.Column(db.String(50))
    funds_source = db.Column(db.String(50))
    franchise_model = db.Column(db.String(50))
    
    # Section 4: Operational Readiness
    has_property = db.Column(db.String(50))
    timeline = db.Column(db.String(50))
    ownership = db.Column(db.String(50))
    property_size = db.Column(db.String(50))
    parking = db.Column(db.String(50))
    accessibility = db.Column(db.String(50))
    workforce = db.Column(db.String(100))
    
    # Section 5: Legal & Compliance
    reg_number = db.Column(db.String(100))
    gst_number = db.Column(db.String(100))
    legal_cases = db.Column(db.Text)
    
    # Section 6: Additional Info
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
    
    def to_dict(self):
        return {
            'id': self.id,
            'issue_type': self.issue_type,
            'description': self.description,
            'status': self.status,
            'charge': self.charge,
            'started_at': self.started_at.strftime('%Y-%m-%d %H:%M') if self.started_at else None,
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M') if self.completed_at else None
        }


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