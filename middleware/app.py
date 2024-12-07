# For API routes and middleware logic.

import os
from flask import Flask, request, jsonify
from google.cloud.sql.connector import Connector
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sys
from dotenv import load_dotenv


# Add the backend folder to sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend"))
sys.path.append(backend_path)

from backend.basic import get_connection
from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app)


# Database configuration
db_user = ""
db_pass = ""
db_name = ""
instance_connection_name = "project-439622:us-central1:sqlpt3stage"

# Load environment variables from .env file
load_dotenv()

# Fetch environment variables
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")

# Initialize Connector
connector = Connector()

# SQLAlchemy setup
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

@app.route("/")
def home():
    return "Welcome to the API! Use specific endpoints like /user, /heatmap or /jobs.", 200

class User(Base):
    __tablename__ = 'User'  # Match the table name in your database (case-sensitive)
    
    UserId = Column(Integer, primary_key=True, autoincrement=True)
    Resume = Column(Text)
    Email = Column(String(255), unique=True, nullable=False)
    Password = Column(String(255), nullable=False)
    FirstName = Column(String(255))
    LastName = Column(String(255))

# Initialize database
Base.metadata.create_all(bind=engine)

@app.route('/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    existing_user = db.query(User).filter_by(username=username).first()
    if existing_user:
        return jsonify({'error': 'User already exists'}), 400

    hashed_password = generate_password_hash(password, method='sha256')
    new_user = User(username=username, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = db.query(User).filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid username or password'}), 401

    # Mock token for simplicity
    token = f"mock-token-for-{username}"
    return jsonify({'message': 'Login successful', 'authToken': token}), 200

# Add and update User information
@app.route('/user', methods=['GET', 'POST', 'PUT'])
def manage_user():
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            if request.method == 'GET':
                # Fetch user information
                email = request.args.get('email')  # Get 'email' query parameter
                if email:
                    # Query for a specific user by email
                    query = "SELECT UserId, Resume, Email, FirstName, LastName FROM User WHERE Email = %s;"
                    cursor.execute(query, (email,))
                else:
                    # Query for all users if no email is provided
                    query = "SELECT UserId, Resume, Email, FirstName, LastName FROM User;"
                    cursor.execute(query)
                
                results = cursor.fetchall()
                users = [
                    {
                        "UserId": row[0],
                        "Resume": row[1],
                        "Email": row[2],
                        "FirstName": row[3],
                        "LastName": row[4]
                    }
                    for row in results
                ]
                return jsonify(users), 200

            elif request.method == 'POST':
                # POST expects JSON
                if not request.is_json:
                    return jsonify({"error": "Request must be JSON and have 'Content-Type: application/json' header"}), 415
                
                # Add new user
                data = request.get_json()
                query = """
                    INSERT INTO User (Resume, Email, Password, FirstName, LastName)
                    VALUES (%s, %s, %s, %s, %s);
                """
                cursor.execute(query, (
                    data.get('Resume'),
                    data['Email'],
                    data['Password'],
                    data.get('FirstName'),
                    data.get('LastName')
                ))
                conn.commit()
                return jsonify({"message": "User added successfully"}), 201

            elif request.method == 'PUT':
                # PUT expects JSON
                if not request.is_json:
                    return jsonify({"error": "Request must be JSON and have 'Content-Type: application/json' header"}), 415
                
                # Update user
                data = request.get_json()
                query = """
                    UPDATE User
                    SET Resume = %s, Password = %s, FirstName = %s, LastName = %s
                    WHERE Email = %s;
                """
                cursor.execute(query, (
                    data.get('Resume'),
                    data['Password'],
                    data.get('FirstName'),
                    data.get('LastName'),
                    data['Email']
                ))
                conn.commit()
                return jsonify({"message": "User updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

# Show filtered jobs
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

    conn = None  # Initialize conn
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
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
                params = []
            cursor.execute(query, params)
            results = cursor.fetchall()
            return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

# Heat map query
@app.route('/heatmap', methods=['GET'])
def heatmap_data():
    city = request.args.get('city')
    state = request.args.get('state')
    zip_code = request.args.get('zip_code')
    
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # Count jobs by nearby locations
            query = """
                SELECT Location.City, Location.State, Location.Latitude, Location.Longitude, COUNT(Job.JobId) as JobCount
                FROM Job
                JOIN Location ON Job.LocationId = Location.LocationId
                WHERE Location.City LIKE %s OR Location.State LIKE %s OR Location.ZipCode LIKE %s
                GROUP BY Location.City, Location.State, Location.Latitude, Location.Longitude;
            """
            cursor.execute(query, (f"%{city}%", f"%{state}%", f"%{zip_code}%"))
            results = cursor.fetchall()
            return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if username in User:
        return jsonify({'error': 'User already exists'}), 400

    hashed_password = generate_password_hash(password, method='sha256')
    User[username] = hashed_password
    return jsonify({'message': 'User registered successfully'}), 201


@app.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if username not in User or not check_password_hash(User[username], password):
        return jsonify({'error': 'Invalid username or password'}), 401

    # Mock token for simplicity (replace with JWT in production)
    token = f"mock-token-for-{username}"
    return jsonify({'message': 'Login successful', 'authToken': token}), 200


if __name__ == '__main__':
    app.run(debug=True)