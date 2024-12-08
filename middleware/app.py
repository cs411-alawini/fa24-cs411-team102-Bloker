# app.py - Updated to support new features
import os

from flask import Flask, request, jsonify
from google.cloud.sql.connector import Connector
import sys


# Add the backend folder to sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend"))
sys.path.append(backend_path)

from basic import get_connection

from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app)


# Database configuration
db_user = "drava"
db_pass = "411pass"
db_name = ""
instance_connection_name = "project-439622:us-central1:sqlpt3stage"

# Initialize Connector
connector = Connector()

import numpy as np
import json
import torch
from transformers import AutoTokenizer, AutoModel

# Initialize the tokenizer and model globally
tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
model.eval()

# Update the cosine similarity function if not already present
def cosine_similarity(v1, v2):
    v1 = np.array(v1)
    v2 = np.array(v2)
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)

# Replace the existing compute_embedding function with this one
def compute_embedding(text):
    inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    # Perform mean pooling on the token embeddings
    embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().tolist()
    return embeddings

@app.route("/")
def home():
    return "Welcome to the API! Use specific endpoints like /user, /heatmap or /jobs.", 200

@app.route('/user', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_user():
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            if request.method == 'GET':
                # Fetch user information
                email = request.args.get('email')  # Get 'email' query parameter
                limit = request.args.get('limit', default=None, type=int)
                if email:
                    # Query for a specific user by email
                    query = "SELECT UserId, Resume, Email, FirstName, LastName FROM User WHERE Email = %s;"
                    cursor.execute(query, (email,))
                else:
                    # Query for all users or limit
                    query = "SELECT UserId, Resume, Email, FirstName, LastName FROM User"
                    params = []
                    if limit:
                        query += " ORDER BY UserId DESC LIMIT %s;"
                        params.append(limit)
                    else:
                        query += ";"
                    cursor.execute(query, params)
                
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

            elif request.method == 'DELETE':
                # Delete user
                email = request.args.get('email')
                if not email:
                    return jsonify({"error": "Email parameter is required for deletion"}), 400

                query = "DELETE FROM User WHERE Email = %s;"
                cursor.execute(query, (email,))
                conn.commit()
                return jsonify({"message": f"User with email {email} deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()
# Show filtered jobs with pagination and city search
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
    filter_params = []

    # Add filters to the query dynamically
    for key, value in filters.items():
        if value:
            where_clauses.append(f"{key} LIKE %s")
            filter_params.append(f"%{value}%")

    offset = request.args.get('offset', default=0, type=int)
    limit = 10  # Default limit

    conn = None  # Initialize conn
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # Build the base query
            query = """
                SELECT Job.JobId, Job.CompanyName, Job.JobRole, Location.City, Location.State, Location.ZipCode
                FROM Job
                JOIN Location ON Job.LocationId = Location.LocationId
                JOIN Company ON Job.CompanyName = Company.CompanyName
            """
            if where_clauses:
                query += " WHERE " + " OR ".join(where_clauses)
            query += " LIMIT %s OFFSET %s;"
            print(query)
            params = filter_params + [limit, offset]
            print(f"Executing query: {cursor.mogrify(query, params)}")  # For debugging
            cursor.execute(query, params)
            results = cursor.fetchall()
            # Convert results to list of dicts for better readability
            jobs = [
                {
                    "JobId": row[0],
                    "CompanyName": row[1],
                    "JobRole": row[2],
                    "City": row[3],
                    "State": row[4],
                    "ZipCode": row[5]
                }
                for row in results
            ]
            return jsonify(jobs), 200
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

@app.route('/auth/login', methods=['POST'])
def login():
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON and have 'Content-Type: application/json' header"}), 415

        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        conn = get_connection()
        with conn.cursor() as cursor:
            query = "SELECT UserId, Resume, ResumeEmbedding, FirstName, LastName FROM User WHERE Email = %s AND Password = %s;"
            cursor.execute(query, (email, password))
            result = cursor.fetchone()

            if not result:
                return jsonify({"error": "Invalid email or password"}), 401

            user_id, resume, resume_embedding, first_name, last_name = result

            # Check and compute ResumeEmbedding if not present
            if not resume_embedding:
                embedding = compute_embedding(resume)
                embedding_json = json.dumps(embedding)
                update_query = "UPDATE User SET ResumeEmbedding = %s WHERE UserId = %s;"
                cursor.execute(update_query, (embedding_json, user_id))
                conn.commit()
                resume_embedding = embedding
            else:
                embedding = json.loads(resume_embedding)

            # Check and compute JobEmbeddings for jobs without them
            job_query = "SELECT JobId, Description FROM Job WHERE JobEmbedding IS NULL;"
            cursor.execute(job_query)
            jobs_to_update = cursor.fetchall()

            for job_id, description in jobs_to_update:
                job_embedding = compute_embedding(description)
                job_embedding_json = json.dumps(job_embedding)
                update_job_query = "UPDATE Job SET JobEmbedding = %s WHERE JobId = %s;"
                cursor.execute(update_job_query, (job_embedding_json, job_id))
            conn.commit()

            return jsonify({
                "message": "Login successful",
                "user": {
                    "UserId": user_id,
                    "Resume": resume,
                    "FirstName": first_name,
                    "LastName": last_name
                }
            }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/user', methods=['GET'])
def get_user():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        conn = get_connection()
        with conn.cursor() as cursor:
            query = "SELECT FirstName, LastName, Resume FROM User WHERE UserId = %s;"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()

            if not result:
                return jsonify({"error": "User not found"}), 404

            first_name, last_name, resume = result

            return jsonify({
                "FirstName": first_name,
                "LastName": last_name,
                "Resume": resume
            }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/auth/register', methods=['POST'])
def register():
    conn = None 
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON and have 'Content-Type: application/json' header"}), 415

        # Get the data from the request body
        data = request.get_json()
        first_name = data.get("firstName")
        last_name = data.get("lastName")
        email = data.get("email")
        password = data.get("password")
        resume = data.get("resume")
        
        # Check if all required fields are provided
        if not all([first_name, last_name, email, password, resume]):
            
            return jsonify({"error": "All fields (FirstName, LastName, Email, Password, Resume) are required"}), 400
        
        # Check if the email already exists in the database
        conn = get_connection()
        with conn.cursor() as cursor:
            query = "SELECT Email FROM User WHERE Email = %s;"
            cursor.execute(query, (email,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                return jsonify({"error": "Email is already in use"}), 400

            # Insert new user data into the User table
            insert_query = """
                INSERT INTO User (FirstName, LastName, Email, Password, Resume)
                VALUES (%s, %s, %s, %s, %s);
            """
            
            cursor.execute(insert_query, (first_name, last_name, email, password, resume))
            conn.commit()
            
            # Return success message
            return jsonify({"message": "Account created successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/recommended', methods=['GET'])
def recommended_jobs():
    print(request.args.get('firstName'))
    conn = None
    try:
        
        user_id = request.args.get('firstName')
        if not user_id:
            return jsonify({"error": "Name is required", "request": request.args}), 400

        conn = get_connection()
        with conn.cursor() as cursor:
            # Retrieve user's resume embedding
            user_query = "SELECT ResumeEmbedding FROM User WHERE FirstName = %s;"
            cursor.execute(user_query, (user_id,))
            user_result = cursor.fetchone()

            if not user_result or not user_result[0]:
                return jsonify({"error": "User embedding not found"}), 404

            user_embedding = json.loads(user_result[0])

            # Retrieve all job embeddings
            job_query = "SELECT JobId, CompanyName, JobRole, Description, JobEmbedding FROM Job;"
            cursor.execute(job_query)
            jobs = cursor.fetchall()

            recommended = []
            for job in jobs:
                job_id, company_name, job_role, description, job_embedding = job
                if not job_embedding:
                    continue  # Skip jobs without embedding

                job_embedding = json.loads(job_embedding)
                similarity = cosine_similarity(user_embedding, job_embedding)

                recommended.append({
                    "JobId": job_id,
                    "CompanyName": company_name,
                    "JobRole": job_role,
                    "Description": description,
                    "Similarity": similarity
                })

            # Sort jobs by similarity in descending order
            recommended_sorted = sorted(recommended, key=lambda x: x["Similarity"], reverse=True)

            # Define the percentage of top jobs to return (e.g., top 10%)
            top_percentage = 10
            top_count = max(1, len(recommended_sorted) * top_percentage // 100)
            top_jobs = recommended_sorted[:top_count]
          
            return jsonify(top_jobs), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    app.run(debug=True)