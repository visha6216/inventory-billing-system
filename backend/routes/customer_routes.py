import logging
from flask import Blueprint, request, jsonify
from config import get_connection
from routes.auth_routes import token_required

customer_bp = Blueprint('customer_bp', __name__)
logger = logging.getLogger("erp_customers")


# =========================
# GET ALL CUSTOMERS
# =========================
@customer_bp.route('/customers', methods=['GET'])
def get_customers():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM customers ORDER BY customer_id DESC")
        customers = cursor.fetchall()
        return jsonify(customers), 200
    except Exception as e:
        logger.error(str(e))
        return jsonify({"error": "Failed to fetch customers"}), 500
    finally:
        if conn:
            conn.close()


# =========================
# GET SINGLE CUSTOMER
# =========================
@customer_bp.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM customers WHERE customer_id = %s", (customer_id,))
        customer = cursor.fetchone()
        if not customer:
            return jsonify({"error": "Customer not found"}), 404
        return jsonify(customer), 200
    except Exception as e:
        logger.error(str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


# =========================
# ADD CUSTOMER
# =========================
@customer_bp.route('/customers', methods=['POST'])
@token_required
def add_customer(current_user_id):
    data = request.json

    name  = data.get('customer_name', '').strip()
    phone = data.get('phone', '').strip()

    if not name:
        return jsonify({"error": "Customer name is required"}), 400
    if not phone:
        return jsonify({"error": "Phone number is required"}), 400

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO customers (
                customer_name, customer_code, email, phone, alt_phone,
                address, city, state, pincode,
                gst_number, pan_number,
                category, subcategory, customer_type, status,
                credit_limit, payment_terms, notes
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s
            )
        """, (
            name,
            data.get('customer_code', ''),
            data.get('email', ''),
            phone,
            data.get('alt_phone', ''),
            data.get('address', ''),
            data.get('city', ''),
            data.get('state', ''),
            data.get('pincode', ''),
            data.get('gst_number', ''),
            data.get('pan_number', ''),
            data.get('category', ''),
            data.get('subcategory', ''),
            data.get('customer_type', 'Regular'),
            data.get('status', 'Active'),
            data.get('credit_limit', 0),
            data.get('payment_terms', 'Immediate'),
            data.get('notes', ''),
        ))
        conn.commit()
        return jsonify({"message": "Customer added successfully", "id": cursor.lastrowid}), 201
    except Exception as e:
        logger.error(str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


# =========================
# UPDATE CUSTOMER
# =========================
@customer_bp.route('/customers/<int:customer_id>', methods=['PUT'])
@token_required
def update_customer(current_user_id, customer_id):
    data = request.json
    name  = data.get('customer_name', '').strip()
    if not name:
        return jsonify({"error": "Customer name is required"}), 400

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE customers SET
                customer_name  = %s, customer_code  = %s, email          = %s,
                phone          = %s, alt_phone      = %s, address        = %s,
                city           = %s, state          = %s, pincode        = %s,
                gst_number     = %s, pan_number     = %s, category       = %s,
                subcategory    = %s, customer_type  = %s, status         = %s,
                credit_limit   = %s, payment_terms  = %s, notes          = %s
            WHERE customer_id = %s
        """, (
            name,
            data.get('customer_code', ''),
            data.get('email', ''),
            data.get('phone', ''),
            data.get('alt_phone', ''),
            data.get('address', ''),
            data.get('city', ''),
            data.get('state', ''),
            data.get('pincode', ''),
            data.get('gst_number', ''),
            data.get('pan_number', ''),
            data.get('category', ''),
            data.get('subcategory', ''),
            data.get('customer_type', 'Regular'),
            data.get('status', 'Active'),
            data.get('credit_limit', 0),
            data.get('payment_terms', 'Immediate'),
            data.get('notes', ''),
            customer_id,
        ))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Customer not found"}), 404
        return jsonify({"message": "Customer updated successfully"}), 200
    except Exception as e:
        logger.error(str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()


# =========================
# DELETE CUSTOMER
# =========================
@customer_bp.route('/customers/<int:customer_id>', methods=['DELETE'])
@token_required
def delete_customer(current_user_id, customer_id):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM customers WHERE customer_id = %s", (customer_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Customer not found"}), 404
        return jsonify({"message": "Customer deleted successfully"}), 200
    except Exception as e:
        logger.error(str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()