import logging
from flask import Blueprint, request, jsonify
from config import get_connection

billing_bp = Blueprint('billing_bp', __name__)

# Configure a dedicated production-grade logger module
logger = logging.getLogger("erp_billing")
logger.setLevel(logging.INFO)

if not logger.handlers:
    file_handler = logging.FileHandler("app_errors.log")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def validate_bill_payload(data):
    """
    Validates the structural and logical integrity of the inbound billing payload.
    """
    if not data:
        return False, "Request payload data body is empty"

    customer_id = data.get('customer_id')
    items = data.get('items', [])

    if not customer_id or not isinstance(customer_id, int):
        return False, "A valid integer customer_id is required"

    if not items or not isinstance(items, list):
        return False, "Items must be a non-empty list structure"

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            return False, f"Item at slot index {index} must be an object"
            
        product_id = item.get('product_id')
        quantity = item.get('quantity', 1)

        if not product_id or not isinstance(product_id, int):
            return False, f"Item index {index} is missing a valid integer product_id"
            
        if not isinstance(quantity, int) or quantity <= 0:
            return False, f"Item index {index} requires a positive, non-zero quantity value"

    return True, None


@billing_bp.route('/bill', methods=['POST'])
def create_bill():
    data = request.json

    # Step 1: Enforce Strict Structural Validation Checks
    is_valid, error_msg = validate_bill_payload(data)
    if not is_valid:
        logger.warning(f"Validation intercept: {error_msg} | Payload context: {data}")
        return jsonify({"error": error_msg}), 400

    customer_id = data.get('customer_id')
    items = data.get('items')

    conn = None
    try:
        conn = get_connection()
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)

        total = 0
        bill_items = []

        # Phase 1: Stock checking & validation using row-locking mechanisms
        for item in items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)

            cursor.execute(
                "SELECT * FROM products WHERE product_id=%s FOR UPDATE",
                (product_id,)
            )
            product = cursor.fetchone()

            if not product:
                conn.rollback()
                logger.error(f"Transaction abort: Product context ID {product_id} not discovered in inventory catalogs.")
                return jsonify({"error": f"Product ID {product_id} not found"}), 404

            if product['stock_quantity'] < quantity:
                conn.rollback()
                logger.warning(f"Transaction intercept: Stock deficit for product ID {product_id}. Requested: {quantity}, Found: {product['stock_quantity']}")
                return jsonify({
                    "error": f"Only {product['stock_quantity']} stock available for {product['product_name']}"
                }), 409

            price = float(product['price'])
            subtotal = price * quantity
            total += subtotal

            bill_items.append({
                "product_id": product_id,
                "product_name": product['product_name'],
                "quantity": quantity,
                "price": price,
                "subtotal": subtotal
            })

        # Calculation matrices
        gst = total * 0.18
        final_total = total + gst

        # Phase 2: Save parent invoice transaction ledger
        cursor.execute("""
            INSERT INTO bills
            (customer_id, total_amount, gst_amount, final_amount)
            VALUES (%s, %s, %s, %s)
        """, (customer_id, total, gst, final_total))
        
        bill_id = cursor.lastrowid

        # Phase 3: Save child mapping items and update stock counts
        for item in bill_items:
            cursor.execute("""
                INSERT INTO bill_items
                (bill_id, product_id, quantity, price, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            """, (bill_id, item['product_id'], item['quantity'], item['price'], item['subtotal']))

            cursor.execute("""
                UPDATE products
                SET stock_quantity = stock_quantity - %s
                WHERE product_id = %s
            """, (item['quantity'], item['product_id']))

        # Complete operations safely
        conn.commit()
        cursor.close()
        
        logger.info(f"Invoice successfully instantiated: Bill ID #{bill_id} | Total: INR {final_total:.2f} | Customer ID: {customer_id}")

        return jsonify({
            "message": "Bill created successfully",
            "bill_id": bill_id,
            "items": bill_items,
            "total": total,
            "gst": gst,
            "final_total": final_total
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()
        logger.critical(f"Critical execution error during bill processing sequence: {str(e)}", exc_info=True)
        return jsonify({"error": "An internal transactional operational error occurred inside the system server."}), 500

    finally:
        if conn:
            conn.close()

@billing_bp.route('/bill-details/<int:bill_id>', methods=['GET'])
def get_bill_details(bill_id):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Fetch the bill header
        cursor.execute("SELECT * FROM bills WHERE bill_id=%s", (bill_id,))
        bill = cursor.fetchone()
        if not bill:
            return jsonify({"error": "Bill not found"}), 404
            
        # Fetch the individual items for this bill
        cursor.execute("""
            SELECT p.product_name, bi.quantity, bi.price, bi.subtotal 
            FROM bill_items bi 
            JOIN products p ON p.product_id = bi.product_id 
            WHERE bi.bill_id = %s
        """, (bill_id,))
        items = cursor.fetchall()
        
        return jsonify({"bill": bill, "items": items})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()