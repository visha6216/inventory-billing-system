"""
Run this as a separate daily cron job:
    python expiry_alert.py

Or schedule it with APScheduler if you want it auto-running inside Flask.
"""
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import get_connection

# ── Configure your Gmail / SMTP here ──────────────────────────────────────────
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
SENDER_EMAIL  = "your_email@gmail.com"       # ← change this
SENDER_PASS   = "your_app_password_here"     # ← use Gmail App Password
ALERT_TO      = "admin@yourcompany.com"      # ← who receives the alert
ALERT_DAYS    = 30                           # warn when expiry is within 30 days
# ──────────────────────────────────────────────────────────────────────────────


def fetch_expiring_products():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.product_id, p.product_name, p.barcode, p.expiry_date,
               p.stock_quantity,
               v.vendor_name, v.vendor_code, v.email AS vendor_email,
               DATEDIFF(p.expiry_date, CURDATE()) AS days_remaining
        FROM products p
        LEFT JOIN vendors v ON p.vendor_id = v.vendor_id
        WHERE p.expiry_date IS NOT NULL
          AND p.expiry_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
        ORDER BY p.expiry_date ASC
    """, (ALERT_DAYS,))
    products = cursor.fetchall()
    conn.close()
    return products


def build_email_body(products):
    rows = ""
    for p in products:
        days = p['days_remaining']
        color = "#ef4444" if days <= 7 else "#f59e0b" if days <= 15 else "#10b981"
        rows += f"""
        <tr>
            <td style="padding:10px;border-bottom:1px solid #2d3142;">{p['product_id']}</td>
            <td style="padding:10px;border-bottom:1px solid #2d3142;">{p['product_name']}</td>
            <td style="padding:10px;border-bottom:1px solid #2d3142;">{p['barcode'] or 'N/A'}</td>
            <td style="padding:10px;border-bottom:1px solid #2d3142;">{p['expiry_date']}</td>
            <td style="padding:10px;border-bottom:1px solid #2d3142;
                       color:{color};font-weight:bold;">{days} days</td>
            <td style="padding:10px;border-bottom:1px solid #2d3142;">{p['stock_quantity']}</td>
            <td style="padding:10px;border-bottom:1px solid #2d3142;">{p['vendor_name'] or 'N/A'}</td>
        </tr>"""

    return f"""
    <html><body style="font-family:Segoe UI,sans-serif;background:#12141c;color:#e4e6eb;padding:20px;">
        <div style="max-width:800px;margin:auto;background:#1a1d29;border-radius:12px;
                    padding:30px;border:1px solid #2d3142;">
            <h2 style="color:#38bdf8;margin-top:0;">
                ⚠️ Product Expiry Pre-Alert — {datetime.date.today()}
            </h2>
            <p style="color:#94a3b8;">
                The following products are expiring within the next <strong>{ALERT_DAYS} days</strong>.
                Please take necessary action.
            </p>
            <table style="width:100%;border-collapse:collapse;margin-top:20px;">
                <thead>
                    <tr style="background:#25293c;">
                        <th style="padding:10px;text-align:left;color:#38bdf8;">ID</th>
                        <th style="padding:10px;text-align:left;color:#38bdf8;">Product</th>
                        <th style="padding:10px;text-align:left;color:#38bdf8;">Barcode</th>
                        <th style="padding:10px;text-align:left;color:#38bdf8;">Expiry Date</th>
                        <th style="padding:10px;text-align:left;color:#38bdf8;">Days Left</th>
                        <th style="padding:10px;text-align:left;color:#38bdf8;">Stock</th>
                        <th style="padding:10px;text-align:left;color:#38bdf8;">Vendor</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
            <p style="color:#64748b;margin-top:20px;font-size:0.85rem;">
                This is an automated alert from your ERP Inventory System.
            </p>
        </div>
    </html></body>"""


def send_expiry_alert():
    products = fetch_expiring_products()

    if not products:
        print(f"[{datetime.datetime.now()}] No products expiring within {ALERT_DAYS} days.")
        return

    print(f"[{datetime.datetime.now()}] Found {len(products)} expiring products. Sending alert...")

    msg = MIMEMultipart("alternative")
    msg['Subject'] = f"⚠️ ERP Expiry Alert — {len(products)} product(s) expiring soon"
    msg['From']    = SENDER_EMAIL
    msg['To']      = ALERT_TO

    msg.attach(MIMEText(build_email_body(products), "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.sendmail(SENDER_EMAIL, ALERT_TO, msg.as_string())

    print(f"[{datetime.datetime.now()}] Alert email sent to {ALERT_TO}")


if __name__ == "__main__":
    send_expiry_alert()