import os
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

# Automatically look up and read from the .env configuration file
load_dotenv()

# Bind configurations dynamically to variables loaded from your environment context
db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "vishal@2005"),
    "database": os.getenv("DB_NAME", "inventory_db")
}

try:
    # Initialize a secure production-grade connection pool (Max 10 reusable slots) using .env configurations
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="erp_pool",
        pool_size=10,
        pool_reset_session=True,
        **db_config
    )
    print("🔒 MySQL Connection Pool bound to environment variables successfully.")
except mysql.connector.Error as err:
    print(f"❌ Connection pool init failed, falling back to basic instances: {err}")
    connection_pool = None

def get_connection():
    """
    Fetches a reusable connection directly from the warm pool context.
    """
    if connection_pool:
        return connection_pool.get_connection()
    else:
        return mysql.connector.connect(**db_config)