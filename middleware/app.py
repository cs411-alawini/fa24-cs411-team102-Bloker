# For API routes and middleware logic.

from flask import Flask, request, jsonify
from google.cloud.sql.connector import Connector
import sys
import os

# Add the backend folder to sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend"))
sys.path.append(backend_path)

from basic import get_connection

app = Flask(__name__)

# Database configuration
db_user = ""
db_pass = ""
db_name = ""
instance_connection_name = "project-439622:us-central1:sqlpt3stage"

# Initialize Connector
connector = Connector()

@app.route("/")
def home():
    return "Welcome to the API! Use specific endpoints like /user, /heatmap or /jobs.", 200

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
                SELECT Location.City, Location.State, COUNT(Job.JobId) as JobCount
                FROM Job
                JOIN Location ON Job.LocationId = Location.LocationId
                WHERE Location.City LIKE %s OR Location.State LIKE %s OR Location.ZipCode LIKE %s
                GROUP BY Location.City, Location.State;
            """
            cursor.execute(query, (f"%{city}%", f"%{state}%", f"%{zip_code}%"))
            results = cursor.fetchall()
            return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)