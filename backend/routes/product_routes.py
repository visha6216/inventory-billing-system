import uuid
import logging
from flask import Blueprint, request, jsonify
from config import get_connection
from routes.auth_routes import token_required

product_bp = Blueprint('product_bp', __name__)
logger = logging.getLogger("erp_products")


# GET ALL PRODUCTS (with vendor + category info joined)
@product_bp.route('/products', methods=['GET'])
def get_products():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.*,
                   v.vendor_name, v.vendor_code,
                   c.category_name,
                   s.subcategory_name
            FROM products p
            LEFT JOIN vendors      v ON p.vendor_id      = v.vendor_id
            LEFT JOIN categories   c ON p.category_id    = c.category_id
            LEFT JOIN subcategories s ON p.subcategory_id = s.subcategory_id
            ORDER BY p.product_id DESC
        """)
        return jsonify(cursor.fetchall()), 200
    except Exception as e:
        logger.error(f"Fetch products error: {str(e)}")
        return jsonify({"error": "Failed to fetch products"}), 500
    finally:
        if conn: conn.close()


# GET EXPIRY ALERTS (products expiring within 30 days)
@product_bp.route('/products/expiry-alerts', methods=['GET'])
def get_expiry_alerts():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.product_id, p.product_name, p.expiry_date, p.barcode,
                   v.vendor_name, v.email AS vendor_email,
                   DATEDIFF(p.expiry_date, CURDATE()) AS days_remaining
            FROM products p
            LEFT JOIN vendors v ON p.vendor_id = v.vendor_id
            WHERE p.expiry_date IS NOT NULL
              AND p.expiry_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
            ORDER BY p.expiry_date ASC
        """)
        return jsonify(cursor.fetchall()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()


# ADD PRODUCT
@product_bp.route('/products', methods=['POST'])
@token_required
def add_product(current_user_id):
    data = request.json
    name             = data.get('product_name')
    stock            = data.get('stock_quantity')
    price            = data.get('price')
    description      = data.get('description', '')
    challan_no       = data.get('challan_no', '')
    vendor_id        = data.get('vendor_id')
    category_id      = data.get('category_id')
    subcategory_id   = data.get('subcategory_id')
    manufactured_date = data.get('manufactured_date')
    expiry_date      = data.get('expiry_date')
    arrived_at       = data.get('arrived_at')

    if not name or stock is None or price is None:
        return jsonify({"error": "Product name, stock and price are required"}), 400

    # Auto-generate unique barcode
    barcode = "BAR-" + str(uuid.uuid4()).upper()[:12]

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products
            (product_name, description, stock_quantity, price, challan_no,
             barcode, vendor_id, category_id, subcategory_id,
             manufactured_date, expiry_date, arrived_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, description, int(stock), float(price), challan_no,
              barcode, vendor_id, category_id, subcategory_id,
              manufactured_date or None, expiry_date or None, arrived_at or None))
        conn.commit()
        return jsonify({
            "message": "Product added successfully",
            "id": cursor.lastrowid,
            "barcode": barcode
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()


# UPDATE PRODUCT
@product_bp.route('/products/<int:pid>', methods=['PUT'])
@token_required
def update_product(current_user_id, pid):
    data = request.json
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE products SET
                product_name=%s, description=%s, stock_quantity=%s, price=%s,
                challan_no=%s, vendor_id=%s, category_id=%s, subcategory_id=%s,
                manufactured_date=%s, expiry_date=%s
            WHERE product_id=%s
        """, (
            data['product_name'], data.get('description'), int(data['stock_quantity']),
            float(data['price']), data.get('challan_no'),
            data.get('vendor_id'), data.get('category_id'), data.get('subcategory_id'),
            data.get('manufactured_date') or None, data.get('expiry_date') or None,
            pid
        ))
        conn.commit()
        return jsonify({"message": "Product updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()


# DELETE PRODUCT
@product_bp.route('/products/<int:pid>', methods=['DELETE'])
@token_required
def delete_product(current_user_id, pid):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE product_id=%s", (pid,))
        conn.commit()
        return jsonify({"message": "Product deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()