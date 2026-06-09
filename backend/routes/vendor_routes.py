import logging
from flask import Blueprint, request, jsonify
from config import get_connection
from routes.auth_routes import token_required

vendor_bp = Blueprint('vendor_bp', __name__)
logger = logging.getLogger("erp_vendors")


# GET ALL VENDORS
@vendor_bp.route('/vendors', methods=['GET'])
def get_vendors():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM vendors ORDER BY vendor_id DESC")
        return jsonify(cursor.fetchall()), 200
    except Exception as e:
        logger.error(str(e))
        return jsonify({"error": "Failed to fetch vendors"}), 500
    finally:
        if conn: conn.close()


# GET SINGLE VENDOR
@vendor_bp.route('/vendors/<int:vendor_id>', methods=['GET'])
def get_vendor(vendor_id):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM vendors WHERE vendor_id = %s", (vendor_id,))
        vendor = cursor.fetchone()
        if not vendor:
            return jsonify({"error": "Vendor not found"}), 404
        return jsonify(vendor), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()


# ADD VENDOR
@vendor_bp.route('/vendors', methods=['POST'])
@token_required
def add_vendor(current_user_id):
    data = request.json
    vendor_name    = data.get('vendor_name', '').strip()
    vendor_code    = data.get('vendor_code', '').strip()
    contact_person = data.get('contact_person', '')
    phone          = data.get('phone', '')
    email          = data.get('email', '')
    address        = data.get('address', '')

    if not vendor_name or not vendor_code:
        return jsonify({"error": "Vendor name and vendor code are required"}), 400

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO vendors (vendor_name, vendor_code, contact_person, phone, email, address)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (vendor_name, vendor_code, contact_person, phone, email, address))
        conn.commit()
        return jsonify({"message": "Vendor added successfully", "id": cursor.lastrowid}), 201
    except Exception as e:
        if "Duplicate entry" in str(e):
            return jsonify({"error": f"Vendor code '{vendor_code}' already exists"}), 409
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()


# UPDATE VENDOR
@vendor_bp.route('/vendors/<int:vendor_id>', methods=['PUT'])
@token_required
def update_vendor(current_user_id, vendor_id):
    data = request.json
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE vendors SET vendor_name=%s, vendor_code=%s, contact_person=%s,
            phone=%s, email=%s, address=%s WHERE vendor_id=%s
        """, (data['vendor_name'], data['vendor_code'], data.get('contact_person'),
              data.get('phone'), data.get('email'), data.get('address'), vendor_id))
        conn.commit()
        return jsonify({"message": "Vendor updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()


# DELETE VENDOR
@vendor_bp.route('/vendors/<int:vendor_id>', methods=['DELETE'])
@token_required
def delete_vendor(current_user_id, vendor_id):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vendors WHERE vendor_id = %s", (vendor_id,))
        conn.commit()
        return jsonify({"message": "Vendor deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()