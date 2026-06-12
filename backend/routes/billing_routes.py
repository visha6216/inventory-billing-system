import logging
from flask import Blueprint, request, jsonify
from config import get_connection

billing_bp = Blueprint('billing_bp', __name__)

logger = logging.getLogger("erp_billing")
logger.setLevel(logging.INFO)

if not logger.handlers:
    file_handler = logging.FileHandler("app_errors.log")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def validate_bill_payload(data):
    if not data:
        return False, "Request payload is empty"
    customer_id = data.get('customer_id')
    items = data.get('items', [])
    if not customer_id or not isinstance(customer_id, int):
        return False, "A valid integer customer_id is required"
    if not items or not isinstance(items, list):
        return False, "Items must be a non-empty list"
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            return False, f"Item at index {index} must be an object"
        product_id = item.get('product_id')
        quantity = item.get('quantity', 1)
        if not product_id or not isinstance(product_id, int):
            return False, f"Item {index} is missing a valid product_id"
        if not isinstance(quantity, int) or quantity <= 0:
            return False, f"Item {index} requires a positive quantity"
    return True, None


@billing_bp.route('/bill', methods=['POST'])
def create_bill():
    data = request.json

    is_valid, error_msg = validate_bill_payload(data)
    if not is_valid:
        logger.warning(f"Validation failed: {error_msg} | Payload: {data}")
        return jsonify({"error": error_msg}), 400

    customer_id  = data.get('customer_id')
    items        = data.get('items')

    # --- FIX: read GST rate, type, and discount from the request ---
    gst_rate     = float(data.get('gst_rate', 18))       # e.g. 18, 5, 28
    gst_type     = data.get('gst_type', 'exclusive')      # 'exclusive' | 'inclusive'
    discount_amt = float(data.get('discount_amt', 0))     # already computed flat amount
    payment_mode = data.get('payment_mode', 'Cash')
    bill_date    = data.get('bill_date')
    due_date     = data.get('due_date')
    notes        = data.get('notes', '')

    conn = None
    try:
        conn = get_connection()
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)

        subtotal   = 0.0
        bill_items = []

        # Phase 1: validate stock and build item list
        for item in items:
            product_id = item.get('product_id')
            quantity   = item.get('quantity', 1)

            cursor.execute(
                "SELECT * FROM products WHERE product_id=%s FOR UPDATE",
                (product_id,)
            )
            product = cursor.fetchone()

            if not product:
                conn.rollback()
                return jsonify({"error": f"Product ID {product_id} not found"}), 404

            if product['stock_quantity'] < quantity:
                conn.rollback()
                return jsonify({
                    "error": f"Only {product['stock_quantity']} units available for '{product['product_name']}'"
                }), 409

            price      = float(product['price'])
            line_total = price * quantity
            subtotal  += line_total

            bill_items.append({
                "product_id":   product_id,
                "product_name": product['product_name'],
                "quantity":     quantity,
                "price":        price,
                "subtotal":     line_total
            })

        # Phase 2: GST & total calculation (mirrors frontend logic exactly)
        taxable = max(0.0, subtotal - discount_amt)

        if gst_type == 'inclusive':
            gst_amount  = taxable - (taxable / (1 + gst_rate / 100))
            final_total = taxable
        else:
            gst_amount  = taxable * gst_rate / 100
            final_total = taxable + gst_amount

        # Phase 3: insert bill record
        cursor.execute("""
            INSERT INTO bills
              (customer_id, total_amount, gst_amount, final_amount,
               gst_rate, gst_type, discount_amt, payment_mode,
               bill_date, due_date, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            customer_id, subtotal, gst_amount, final_total,
            gst_rate, gst_type, discount_amt, payment_mode,
            bill_date, due_date, notes
        ))

        bill_id = cursor.lastrowid

        # Phase 4: insert bill items & deduct stock
        for item in bill_items:
            cursor.execute("""
                INSERT INTO bill_items (bill_id, product_id, quantity, price, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            """, (bill_id, item['product_id'], item['quantity'], item['price'], item['subtotal']))

            cursor.execute("""
                UPDATE products SET stock_quantity = stock_quantity - %s
                WHERE product_id = %s
            """, (item['quantity'], item['product_id']))

        conn.commit()
        cursor.close()

        logger.info(f"Bill #{bill_id} created | Customer: {customer_id} | Total: ₹{final_total:.2f}")

        return jsonify({
            "message":     "Bill created successfully",
            "bill_id":     bill_id,
            "items":       bill_items,
            "subtotal":    subtotal,
            "discount":    discount_amt,
            "gst_amount":  gst_amount,
            "final_total": final_total
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()
        logger.critical(f"Bill creation error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error during bill creation"}), 500

    finally:
        if conn:
            conn.close()


@billing_bp.route('/bill-details/<int:bill_id>', methods=['GET'])
def get_bill_details(bill_id):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM bills WHERE bill_id=%s", (bill_id,))
        bill = cursor.fetchone()
        if not bill:
            return jsonify({"error": "Bill not found"}), 404

        # FIX: filter by bill_id so only THIS bill's items are returned
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
        if conn:
            conn.close()