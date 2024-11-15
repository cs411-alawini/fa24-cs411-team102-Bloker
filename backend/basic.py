import os
from google.cloud.sql.connector import Connector

# Ensure the GOOGLE_APPLICATION_CREDENTIALS environment variable is set
assert "GOOGLE_APPLICATION_CREDENTIALS" in os.environ, "GOOGLE_APPLICATION_CREDENTIALS is not set!"

# Database connection configuration
db_user = "sike"
db_pass = "sike"
db_name = "sike"

INSTANCE_CONNECTION_NAME = os.getenv(
    "INSTANCE_CONNECTION_NAME", "project-439622:us-central1:sqlpt3stage"
)

print(f"Your instance connection name is: {INSTANCE_CONNECTION_NAME}")
print(db_pass)

# Initialize Connector
connector = Connector()

# Function to return the database connection object
def get_connection():
    conn = connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pymysql",
        user=db_user,
        password=db_pass,
        db=db_name,
    )
    return conn

def query_database():
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # Example query: Fetch all users
            query = "SELECT * FROM User LIMIT 10;"
            cursor.execute(query)
            
            # Fetch results
            results = cursor.fetchall()
            print("Query Results:")
            for row in results:
                print(row)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

# build out specific queries

if __name__ == "__main__":
    query_database()

