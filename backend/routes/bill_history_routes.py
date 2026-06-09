import logging
from flask import Blueprint, request, jsonify
from config import get_connection

bill_history_bp = Blueprint('bill_history_bp', __name__)

logger = logging.getLogger("erp_history")
logger.setLevel(logging.INFO)

@bill_history_bp.route('/bill-history', methods=['GET'])
def get_bill_history():
    conn = None
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        search_customer = request.args.get('customer_id', '').strip()

        offset = (page - 1) * limit

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        data_query = "SELECT * FROM bills"
        count_query = "SELECT COUNT(*) AS total_records FROM bills"
        query_params = []

        if search_customer and search_customer.isdigit():
            where_clause = " WHERE customer_id = %s"
            data_query += where_clause
            count_query += where_clause
            query_params.append(int(search_customer))

        data_query += " ORDER BY bill_id DESC LIMIT %s OFFSET %s"
        
        cursor.execute(count_query, tuple(query_params))
        total_records = cursor.fetchone()['total_records']

        extended_params = query_params + [limit, offset]
        cursor.execute(data_query, tuple(extended_params))
        bills = cursor.fetchall()

        cursor.close()

        total_pages = (total_records + limit - 1) // limit

        return jsonify({
            "bills": bills,
            "pagination": {
                "current_page": page,
                "limit": limit,
                "total_records": total_records,
                "total_pages": total_pages
            }
        }), 200

    except Exception as e:
        logger.critical(f"Failed to fetch segmented bill history logs: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error reading historic data records."}), 500

    finally:
        if conn:
            conn.close()