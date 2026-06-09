import logging
from flask import Blueprint, jsonify
from config import get_connection

dashboard_bp = Blueprint('dashboard_bp', __name__)

logger = logging.getLogger("erp_dashboard")
logger.setLevel(logging.INFO)

@dashboard_bp.route('/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Count Total Unique Products in Inventory
        cursor.execute("SELECT COUNT(*) AS total_products FROM products")
        products_res = cursor.fetchone()
        total_products = products_res['total_products'] if products_res else 0

        # 2. Count Total Unique Registered Corporate Clients
        cursor.execute("SELECT COUNT(*) AS total_customers FROM customers")
        customers_res = cursor.fetchone()
        total_customers = customers_res['total_customers'] if customers_res else 0

        # 3. Count Total Generated Bills Invoices
        cursor.execute("SELECT COUNT(*) AS total_bills FROM bills")
        bills_res = cursor.fetchone()
        total_bills = bills_res['total_bills'] if bills_res else 0

        # 4. Sum up Gross Consolidated Revenue Safely
        # COALESCE ensures that if the sum is NULL (empty table), it returns 0 instead of breaking
        cursor.execute("""
            SELECT COALESCE(SUM(CAST(final_amount AS DECIMAL(10,2))), 0.00) AS total_revenue 
            FROM bills
        """)
        revenue_res = cursor.fetchone()
        total_revenue = float(revenue_res['total_revenue']) if revenue_res else 0.0

        # 5. Calculate monthly trend analysis loops for your Chart.js visualization
        # This groups the last 6 months of historical transactions cleanly
        cursor.execute("""
            SELECT COALESCE(SUM(CAST(final_amount AS DECIMAL(10,2))), 0.00) AS month_total 
            FROM bills 
            GROUP BY MONTH(created_at) 
            LIMIT 6
        """)
        trend_res = cursor.fetchall()
        
        # Build array matrix for chart, fallback to zeros if history is empty
        revenue_trend = [float(row['month_total']) for row in trend_res]
        while len(revenue_trend) < 6:
            revenue_trend.append(0.0)

        cursor.close()

        # Return a uniform distribution payload block to match your script.js expectations
        return jsonify({
            "total_products": total_products,
            "total_customers": total_customers,
            "total_bills": total_bills,
            "total_revenue": total_revenue,
            "revenue_trend": revenue_trend
        }), 200

    except Exception as e:
        logger.critical(f"Dashboard data gathering engine crash exception: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Failed to pull unified dashboard matrices context records.",
            "total_products": 0,
            "total_customers": 0,
            "total_bills": 0,
            "total_revenue": 0.00,
            "revenue_trend": [0, 0, 0, 0, 0, 0]
        }), 500

    finally:
        if conn:
            conn.close()