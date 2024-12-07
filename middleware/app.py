import os
from flask import Flask, request, jsonify
from google.cloud.sql.connector import Connector
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app and CORS
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:8000"}}, supports_credentials=True)

# Database configuration
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")

# SQLAlchemy setup
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Define SQLAlchemy User model
class User(Base):
    __tablename__ = 'User'

    UserId = Column(Integer, primary_key=True, autoincrement=True)
    Resume = Column(Text)
    Email = Column(String(255), unique=True, nullable=False)
    Password = Column(String(255), nullable=False)
    FirstName = Column(String(255))
    LastName = Column(String(255))

# Initialize database tables
Base.metadata.create_all(bind=engine)

@app.after_request
def after_request(response):
    """Add CORS headers to all responses."""
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response

# Handle preflight requests
@app.route('/auth/register', methods=['OPTIONS'])
@app.route('/auth/login', methods=['OPTIONS'])
def handle_preflight():
    """Handle preflight requests."""
    response = jsonify({'message': 'Preflight request allowed'})
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:8000')
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

        if db.query(User).filter_by(Email=email).first():
            return jsonify({'error': 'User already exists'}), 400

        hashed_password = generate_password_hash(password, method='sha256')
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
        return jsonify({'error': str(e)}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    """User login endpoint."""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

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
    
    where_clauses = []
    params = []

    # Add filters to the query dynamically
    for key, value in filters.items():
        if value:
            where_clauses.append(f"{key} LIKE %s")
            params.append(f"%{value}%")

    try:
        with pool.cursor() as cursor:
            if where_clauses:
                query = f"""
                    SELECT Job.JobId, Job.CompanyName, Job.JobRole, Location.City, Location.State, Location.ZipCode
                    FROM Job
                    JOIN Location ON Job.LocationId = Location.LocationId
                    JOIN Company ON Job.CompanyName = Company.CompanyName
                    WHERE {' OR '.join(where_clauses)}
                    LIMIT 10;
                """
            else:
                query = """
                    SELECT Job.JobId, Job.CompanyName, Job.JobRole, Location.City, Location.State, Location.ZipCode
                    FROM Job
                    JOIN Location ON Job.LocationId = Location.LocationId
                    JOIN Company ON Job.CompanyName = Company.CompanyName
                    LIMIT 10;
                """
            cursor.execute(query, params)
            results = cursor.fetchall()
            return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)