import mysql.connector
from mysql.connector import Error
from config import DATABASE_CONFIG

class Database:
    def __init__(self):
        self.connection = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(**DATABASE_CONFIG)
            if self.connection.is_connected():
                print("Connected to the database")
        except Error as e:
            print(f"Error: {e}")

    def disconnect(self):
        if self.connection.is_connected():
            self.connection.close()
            print("Disconnected from the database")

    def execute_query(self, query, params=None):
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params)
            self.connection.commit()
            return cursor.fetchall()
        except Error as e:
            print(f"Error: {e}")
            return None

    def execute_update(self, query, params=None):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            print("Update executed successfully")
        except Error as e:
            print(f"Error: {e}")