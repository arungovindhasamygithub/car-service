import os

class Config:
    SECRET_KEY = 'your-secret-key-change-this'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///car_service.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    UPI_ID = "careservice@okhdfcbank"