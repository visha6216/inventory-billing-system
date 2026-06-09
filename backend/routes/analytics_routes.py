import logging
from flask import Blueprint, request, jsonify
from config import get_connection

analytics_bp = Blueprint('analytics_bp', __name__)
logger = logging.getLogger("erp_analytics")


# =========================
# SALES SUMMARY
# =========================
@analytics_bp.route('/analytics/summary', methods=['GET'])
def get_summary():
    days = request.args.get('days', 'all')
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        where = ""
        params = []
        if days != 'all':
            where = "WHERE b.bill_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)"
            params = [int(days)]

        cursor.execute(f"""
            SELECT
                COUNT(DISTINCT b.bill_id)           AS total_bills,
                COALESCE(SUM(b.final_amount), 0)    AS total_revenue,
                COALESCE(SUM(b.gst_amount), 0)      AS total_gst,
                COALESCE(SUM(b.total_amount), 0)    AS subtotal,
                COUNT(DISTINCT b.customer_id)       AS unique_customers,
                COALESCE(SUM(bi.quantity), 0)       AS items_sold
            FROM bills b
            LEFT JOIN bill_items bi ON bi.bill_id = b.bill_id
            {where}
        """, params)
        summary = cursor.fetchone()
        return jsonify(summary), 200
    except Exception as e:
        logger.error(str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()


# =========================
# TOP SELLING PRODUCTS
# =========================
@analytics_bp.route('/analytics/top-products', methods=['GET'])
def get_top_products():
    days  = request.args.get('days', '30')
    limit = int(request.args.get('limit', 10))
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        where = ""
        params = []
        if days != 'all':
            where = "AND b.bill_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)"
            params = [int(days)]

        cursor.execute(f"""
            SELECT
                p.product_id,
                p.product_name,
                SUM(bi.quantity)    AS total_qty,
                SUM(bi.subtotal)    AS total_revenue,
                COUNT(DISTINCT bi.bill_id) AS bill_count
            FROM bill_items bi
            JOIN products p ON p.product_id = bi.product_id
            JOIN bills b    ON b.bill_id    = bi.bill_id
            WHERE 1=1 {where}
            GROUP BY p.product_id, p.product_name
            ORDER BY total_qty DESC
            LIMIT %s
        """, params + [limit])

        return jsonify(cursor.fetchall()), 200
    except Exception as e:
        logger.error(str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()


# =========================
# TOP CUSTOMERS
# =========================
@analytics_bp.route('/analytics/top-customers', methods=['GET'])
def get_top_customers():
    days  = request.args.get('days', '30')
    limit = int(request.args.get('limit', 10))
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        where = ""
        params = []
        if days != 'all':
            where = "WHERE b.bill_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)"
            params = [int(days)]

        cursor.execute(f"""
            SELECT
                c.customer_id,
                c.customer_name,
                c.gst_number,
                c.phone,
                COUNT(b.bill_id)        AS total_bills,
                SUM(b.final_amount)     AS total_spent,
                SUM(b.gst_amount)       AS gst_paid,
                MAX(b.bill_date)        AS last_purchase
            FROM bills b
            JOIN customers c ON c.customer_id = b.customer_id
            {where}
            GROUP BY c.customer_id, c.customer_name, c.gst_number, c.phone
            ORDER BY total_spent DESC
            LIMIT %s
        """, params + [limit])

        return jsonify(cursor.fetchall()), 200
    except Exception as e:
        logger.error(str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()


# =========================
# REVENUE TREND (daily)
# =========================
@analytics_bp.route('/analytics/revenue-trend', methods=['GET'])
def get_revenue_trend():
    days = request.args.get('days', '30')
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        where = ""
        params = []
        if days != 'all':
            where = "WHERE bill_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)"
            params = [int(days)]

        cursor.execute(f"""
            SELECT
                DATE(bill_date)             AS date,
                COUNT(bill_id)              AS bill_count,
                SUM(final_amount)           AS revenue,
                SUM(gst_amount)             AS gst
            FROM bills
            {where}
            GROUP BY DATE(bill_date)
            ORDER BY date ASC
        """, params)

        return jsonify(cursor.fetchall()), 200
    except Exception as e:
        logger.error(str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()


# =========================
# STOCK ALERTS
# =========================
@analytics_bp.route('/analytics/stock-alerts', methods=['GET'])
def get_stock_alerts():
    threshold = int(request.args.get('threshold', 10))
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                p.product_id, p.product_name, p.stock_quantity,
                p.price, v.vendor_name,
                (p.stock_quantity * p.price) AS stock_value
            FROM products p
            LEFT JOIN vendors v ON v.vendor_id = p.vendor_id
            WHERE p.stock_quantity <= %s
            ORDER BY p.stock_quantity ASC
        """, (threshold,))
        return jsonify(cursor.fetchall()), 200
    except Exception as e:
        logger.error(str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()