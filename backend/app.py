import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Single CORS call — allows all origins (works for local dev)
CORS(app)

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "fallback_default_key_change_me")

# =========================
# IMPORT ALL ROUTES
# =========================
from routes.product_routes      import product_bp
from routes.customer_routes     import customer_bp
from routes.billing_routes      import billing_bp
from routes.bill_history_routes import bill_history_bp
from routes.dashboard_routes    import dashboard_bp
from routes.auth_routes         import auth_bp
from routes.invoice_routes      import invoice_bp
from routes.vendor_routes       import vendor_bp
from routes.category_routes     import category_bp
from routes.analytics_routes    import analytics_bp

# =========================
# REGISTER ALL ROUTES
# =========================
app.register_blueprint(product_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(billing_bp)
app.register_blueprint(bill_history_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(invoice_bp)
app.register_blueprint(vendor_bp)
app.register_blueprint(category_bp)
app.register_blueprint(analytics_bp)

# =========================
# HOME ROUTE
# =========================
@app.route('/')
def home():
    return {"message": "Inventory Billing System Backend Running"}

# =========================
# RUN SERVER
# =========================
if __name__ == '__main__':
    host_ip    = os.getenv("HOST", "127.0.0.1")
    port_num   = int(os.getenv("PORT", 5000))
    debug_state = os.getenv("FLASK_DEBUG", "True") == "True"

    print(f"🚀 ERP Engine running on http://{host_ip}:{port_num}")
    app.run(host=host_ip, port=port_num, debug=debug_state)