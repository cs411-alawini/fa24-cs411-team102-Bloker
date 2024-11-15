import os

DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "your-gcp-host"),
    "user": os.getenv("DB_USER", "your-username"),
    "password": os.getenv("DB_PASSWORD", "your-password"),
    "database": os.getenv("DB_NAME", "411project")
}