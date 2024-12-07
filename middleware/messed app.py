import os
import pymysql
import pg8000
import logging
from flask import Flask, request, jsonify
from google.cloud.sql.connector import Connector
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, Text, DECIMAL, Date, ForeignKey, Table, create_engine
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from flask_cors import CORS
from dotenv import load_dotenv
from contextlib import contextmanager

# logging.basicConfig()
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app and CORS
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:8000"}}, supports_credentials=True)

# Database configuration
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")

connector = Connector()

def get_connection():
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")
    db = os.getenv("DB_NAME")
    instance = os.getenv("INSTANCE_CONNECTION_NAME")

    if not all([user, password, db, instance]):
        raise ValueError("One or more required database environment variables are missing.")

    try:
        print(f"Attempting connection as user: {user} to instance: {instance}")  # Debug info
        return connector.connect(
            instance,
            "pymysql",
            user=user,
            password=password,
            db=db
        )
    except Exception as e:
        print(f"Database connection failed: {e}")  # Log the error
        raise

# Use the connection factory
engine = create_engine(
    "mysql+pymysql://",
    creator=get_connection
)

# SQLAlchemy setup
# DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
# engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)
# db = SessionLocal()

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Define SQLAlchemy models
# User Model
class User(Base):
    __tablename__ = 'User'

    UserId = Column(Integer, primary_key=True, autoincrement=True)
    Resume = Column(Text)
    Email = Column(String(255), unique=True, nullable=False)
    Password = Column(String(255), nullable=False)
    FirstName = Column(String(255))
    LastName = Column(String(255))
    experiences = relationship("Experience", back_populates="user", cascade="all, delete")
    user_jobs = relationship("UserJob", back_populates="user", cascade="all, delete")


# Company Model
class Company(Base):
    __tablename__ = 'Company'

    CompanyName = Column(String(255), primary_key=True)
    Industry = Column(String(255))
    CompanySize = Column(Integer)


# Location Model
class Location(Base):
    __tablename__ = 'Location'

    LocationId = Column(Integer, primary_key=True, autoincrement=True)
    City = Column(String(255))
    State = Column(String(255))
    ZipCode = Column(String(10))
    Country = Column(String(255))


# Experience Model
class Experience(Base):
    __tablename__ = 'Experience'

    ExperienceId = Column(Integer, primary_key=True, autoincrement=True)
    UserId = Column(Integer, ForeignKey('User.UserId', ondelete="CASCADE"), nullable=False)
    StartDate = Column(Date)
    EndDate = Column(Date)
    Achievement = Column(Text)
    Skills = Column(Text)
    user = relationship("User", back_populates="experiences")


# Job Model
class Job(Base):
    __tablename__ = 'Job'

    JobId = Column(Integer, primary_key=True, autoincrement=True)
    CompanyName = Column(String(255), ForeignKey('Company.CompanyName'))
    JobRole = Column(String(255))
    LocationId = Column(Integer, ForeignKey('Location.LocationId'))
    Description = Column(Text)
    MinSalary = Column(DECIMAL(10, 2))
    MaxSalary = Column(DECIMAL(10, 2))
    Skills = Column(Text)
    company = relationship("Company")
    location = relationship("Location")
    job_locations = relationship("JobLocation", back_populates="job")
    user_jobs = relationship("UserJob", back_populates="job")


# JobLocation Model
class JobLocation(Base):
    __tablename__ = 'JobLocation'

    JobId = Column(Integer, ForeignKey('Job.JobId'), primary_key=True)
    LocationId = Column(Integer, ForeignKey('Location.LocationId'), primary_key=True)
    job = relationship("Job", back_populates="job_locations")
    location = relationship("Location")


# UserJob Model
class UserJob(Base):
    __tablename__ = 'UserJob'

    UserId = Column(Integer, ForeignKey('User.UserId', ondelete="CASCADE"), primary_key=True)
    JobId = Column(Integer, ForeignKey('Job.JobId', ondelete="CASCADE"), primary_key=True)
    ApplicationDate = Column(Date)
    Status = Column(String(50))
    user = relationship("User", back_populates="user_jobs")
    job = relationship("Job", back_populates="user_jobs")

# Initialize database tables
Base.metadata.create_all(bind=engine)

@app.after_request
def after_request(response):
    """Ensure other headers are set, but let flask_cors handle CORS."""
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response

# Handle preflight requests
@app.route('/auth/register', methods=['OPTIONS'])
@app.route('/auth/login', methods=['OPTIONS'])
def handle_preflight():
    """Handle preflight requests."""
    response = jsonify({'message': 'Preflight request allowed'})
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response, 200

# Routes
@app.route("/")
def home():
    return "Welcome to the API! Use specific endpoints like /user, /heatmap, or /jobs.", 200

@app.route('/auth/register', methods=['POST'])
def register():
    """User registration endpoint."""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('firstName')
        last_name = data.get('lastName')

        # Input validation
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        with get_db() as db:
            # Check if the user already exists
            if db.query(User).filter_by(Email=email).first():
                return jsonify({'error': 'User already exists'}), 400

            # Hash the password
            hashed_password = generate_password_hash(password, method='sha256')

            # Create new user
            new_user = User(
                Email=email,
                Password=hashed_password,
                FirstName=first_name,
                LastName=last_name
            )
            db.add(new_user)
            db.commit()

        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        print(f"Error during registration: {e}")  # Debugging
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    """User login endpoint."""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        with get_db() as db:
            user = db.query(User).filter_by(Email=email).first()
            if not user or not check_password_hash(user.Password, password):
                return jsonify({'error': 'Invalid email or password'}), 401

        token = f"mock-token-for-{email}"  # Replace with JWT in production
        return jsonify({'message': 'Login successful', 'authToken': token}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/jobs', methods=['GET'])
def get_jobs():
    filters = {
        'CompanyName': request.args.get('company_name'),
        'JobRole': request.args.get('job_role'),
        'Industry': request.args.get('industry'),
        'City': request.args.get('city'),
        'State': request.args.get('state'),
        'ZipCode': request.args.get('zip_code')
    }
    
    with get_db() as db:
        query = db.query(Job, Location, Company).join(Location).join(Company)
        for key, value in filters.items():
            if value:
                query = query.filter(getattr(Job, key).like(f"%{value}%"))
        results = query.limit(10).all()

    return jsonify([{
        "JobId": job.JobId,
        "CompanyName": job.CompanyName,
        "JobRole": job.JobRole,
        "City": location.City,
        "State": location.State,
        "ZipCode": location.ZipCode
    } for job, location, company in results]), 200

if __name__ == '__main__':
    app.run(debug=True)