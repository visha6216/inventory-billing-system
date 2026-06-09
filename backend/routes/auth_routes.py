import jwt
import datetime
from flask import Blueprint, request, jsonify
from functools import wraps
from config import get_connection

auth_bp = Blueprint('auth_bp', __name__)

# Secret key used to sign and verify JWT tokens 
SECRET_KEY = "vishal_super_hidden_erp_jwt_string_2026"

def token_required(f):
    """
    Custom decorator to guard routes against unauthenticated access.
    Extracts, cleans, and decodes incoming Bearer tokens.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if the Authorization header is present
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Security access token is missing or expired"}), 401

        try:
            # Decode the token signature using our global secret key
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user_id = data.get('user_id')
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Session expired. Please log in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token signature verification failed"}), 401

        # Pass the extracted user context down to the protected route function
        return f(current_user_id, *args, **kwargs)

    return decorated


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticates system users and returns a valid JWT session token.
    """
    data = request.json
    if not data:
        return jsonify({"error": "No credentials provided"}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Look up the user record safely from the database
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()

        # Simple string comparison or password hash match verification block
        if user and user['password'] == password:
            # Generate a session token valid for 8 hours
            token = jwt.encode({
                'user_id': user['user_id'],
                'username': user['username'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=8)
            }, SECRET_KEY, algorithm='HS256')

            return jsonify({
                "message": "Login successful",
                "token": token,
                "user": {
                    "user_id": user['user_id'],
                    "username": user['username']
                }
            }), 200
        
        return jsonify({"error": "Invalid username or password credentials"}), 401

    except Exception as e:
        return jsonify({"error": f"Authentication operational failure: {str(e)}"}), 500
        
    finally:
        if conn:
            conn.close()