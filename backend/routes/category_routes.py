from flask import Blueprint, request, jsonify
from config import get_connection
from routes.auth_routes import token_required

category_bp = Blueprint('category_bp', __name__)


# GET ALL CATEGORIES WITH THEIR SUBCATEGORIES
@category_bp.route('/categories', methods=['GET'])
def get_categories():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM categories ORDER BY category_name")
        categories = cursor.fetchall()

        for cat in categories:
            cursor.execute(
                "SELECT * FROM subcategories WHERE category_id = %s",
                (cat['category_id'],)
            )
            cat['subcategories'] = cursor.fetchall()

        return jsonify(categories), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()


# ADD CATEGORY
@category_bp.route('/categories', methods=['POST'])
@token_required
def add_category(current_user_id):
    data = request.json
    name = data.get('category_name', '').strip()
    if not name:
        return jsonify({"error": "Category name is required"}), 400
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO categories (category_name) VALUES (%s)", (name,))
        conn.commit()
        return jsonify({"message": "Category added", "id": cursor.lastrowid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()


# ADD SUBCATEGORY
@category_bp.route('/subcategories', methods=['POST'])
@token_required
def add_subcategory(current_user_id):
    data = request.json
    name        = data.get('subcategory_name', '').strip()
    category_id = data.get('category_id')
    if not name or not category_id:
        return jsonify({"error": "Subcategory name and category_id are required"}), 400
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO subcategories (subcategory_name, category_id) VALUES (%s, %s)",
            (name, category_id)
        )
        conn.commit()
        return jsonify({"message": "Subcategory added", "id": cursor.lastrowid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()


# DELETE CATEGORY
@category_bp.route('/categories/<int:cid>', methods=['DELETE'])
@token_required
def delete_category(current_user_id, cid):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE category_id = %s", (cid,))
        conn.commit()
        return jsonify({"message": "Category deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()


# DELETE SUBCATEGORY
@category_bp.route('/subcategories/<int:sid>', methods=['DELETE'])
@token_required
def delete_subcategory(current_user_id, sid):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM subcategories WHERE subcategory_id = %s", (sid,))
        conn.commit()
        return jsonify({"message": "Subcategory deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()