import os
from flask import Blueprint, send_file, make_response
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
from config import get_connection
import qrcode

invoice_bp = Blueprint('invoice_bp', __name__)

@invoice_bp.route('/invoice/<int:bill_id>', methods=['GET'])
def generate_invoice(bill_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # 1. Fetch Master Bill Information Profile Record
    cursor.execute("SELECT * FROM bills WHERE bill_id=%s", (bill_id,))
    bill = cursor.fetchone()

    if not bill:
        return {"error": "Bill data structural record not located"}, 404

    # 2. Fetch Customer Account Data Attributes
    cursor.execute("SELECT * FROM customers WHERE customer_id=%s", (bill['customer_id'],))
    customer = cursor.fetchone()

    # 3. Fetch Dynamic Transaction Item Data Matrices Linked specifically to this Active Run
    cursor.execute("""
        SELECT
            p.product_name,
            bi.quantity,
            bi.price,
            bi.subtotal
        FROM bill_items bi
        JOIN products p ON p.product_id = bi.product_id
        WHERE bi.bill_id=%s
    """, (bill_id,))
    items = cursor.fetchall()

    # Initialize Canvas Vector Coordinates Engine Frameworks
    pdf_buffer = BytesIO()
    p = canvas.Canvas(pdf_buffer)
    
    width = 595   # Standard A4 Width Point System Constraints
    height = 842  # Standard A4 Height Point System Constraints

    # ----------------------------------------------------------------------
    # MASTER HEADER SECTION (Deep Corporate Blue Block)
    # ----------------------------------------------------------------------
    p.setFillColor(colors.HexColor("#0F4C81"))
    p.rect(0, 750, width, 92, fill=1)

    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 22)
    p.drawString(40, 798, "INVENTORY BILLING SYSTEM")

    # Hardcoded Request Updates mapping branding requirements explicitly
    p.setFont("Helvetica", 10)
    p.drawString(40, 780, "Khopoli, Maharashtra")
    p.drawString(40, 765, "Mobile: ") 

    # Dynamic QR Code Compilations (Top-Right Core Matrix Position Layout)
    invoice_url = f"http://127.0.0.1:5000/invoice/{bill_id}"
    qr = qrcode.make(invoice_url)
    qr_path = f"qr_{bill_id}.png"
    qr.save(qr_path)

    p.drawImage(qr_path, 475, 756, width=68, height=68)

    # ----------------------------------------------------------------------
    # DOCUMENT META IDENTIFICATION TEXT FIELDS
    # ----------------------------------------------------------------------
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 18)
    p.drawString(40, 705, "TAX INVOICE")

    p.setFont("Helvetica", 10)
    p.setFillColor(colors.HexColor("#334155"))
    p.drawString(40, 682, f"Invoice No: {bill['bill_id']}")
    p.drawString(40, 666, f"Date: {bill['bill_date']}")

    # ----------------------------------------------------------------------
    # CUSTOMER ACCOUNT PROFILE CONTAINER BOX
    # ----------------------------------------------------------------------
    p.setFillColor(colors.HexColor("#F8FAFC")) # Smooth modern tint frame mix
    p.setStrokeColor(colors.HexColor("#E2E8F0"))
    p.rect(40, 560, 515, 82, fill=1, stroke=1)

    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(55, 622, "Bill To:")

    p.setFont("Helvetica", 10)
    p.setFillColor(colors.HexColor("#1E293B"))
    p.drawString(55, 602, f"Name: {customer['customer_name'] if customer else 'N/A'}")
    p.drawString(55, 584, f"Phone: {customer['phone'] if customer else 'N/A'}")
    p.drawString(280, 602, f"Email: {customer['email'] if customer else 'N/A'}")
    p.drawString(280, 584, f"Address: {customer['address'] if customer else 'N/A'}")

    # ----------------------------------------------------------------------
    # ITEMIZED TRANSACTIONS LEDGER TABLE COMPONENT
    # ----------------------------------------------------------------------
    # Table Header Fields Decoration
    p.setFillColor(colors.HexColor("#D9EAF7"))
    p.setStrokeColor(colors.HexColor("#CBD5E1"))
    p.rect(40, 515, 515, 26, fill=1, stroke=1)

    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(55, 523, "Product Description")
    p.drawCentredString(320, 523, "Quantity")
    p.drawRightString(535, 523, "Price")

    # Render dynamic table row coordinates matrices loop
    y_position = 490
    subtotal_aggregate = 0.0
    
    p.setFont("Helvetica", 10)
    p.setFillColor(colors.HexColor("#334155"))

    for item in items:
        if y_position < 280: 
            p.setFont("Helvetica-Oblique", 8)
            p.drawString(40, y_position, "* Additional items truncated due to space limits.")
            break
            
        p.drawString(55, y_position, str(item['product_name']))
        p.drawCentredString(320, y_position, str(item['quantity']))
        p.drawRightString(535, y_position, f"₹ {float(item['price']):,.2f}")

        subtotal_aggregate += float(item['subtotal'])
        y_position -= 24

    # Horizontal Border Separator Matrix System Line Rule
    p.setStrokeColor(colors.HexColor("#E2E8F0"))
    p.setLineWidth(1)
    p.line(40, y_position + 10, 555, y_position + 10)

    # Render Subtotal Calculations Summary Line row item
    y_position -= 10
    p.setFont("Helvetica-Bold", 10)
    p.setFillColor(colors.HexColor("#1E293B"))
    p.drawString(340, y_position, "Subtotal:")
    p.drawRightString(535, y_position, f"₹ {subtotal_aggregate:,.2f}")

    # ----------------------------------------------------------------------
    # FINANCIAL COMPUTATION BALANCES MATRIX DISPLAY BOX
    # ----------------------------------------------------------------------
    totals_box_y = max(140, y_position - 110)

    p.setFillColor(colors.HexColor("#F8FAFC"))
    p.setStrokeColor(colors.HexColor("#CBD5E1"))
    p.rect(315, totals_box_y, 240, 85, fill=1, stroke=1)

    p.setFillColor(colors.HexColor("#334155"))
    p.setFont("Helvetica-Bold", 10)
    p.drawString(335, totals_box_y + 60, "Total Amount:")
    p.drawString(335, totals_box_y + 38, "GST (18%):")
    
    p.setFillColor(colors.HexColor("#0F4C81"))
    p.setFont("Helvetica-Bold", 12)
    p.drawString(335, totals_box_y + 14, "Grand Total:")

    # Map transaction values requested by user cleanly with hardcoded alignment tracking overrides
    p.setFillColor(colors.HexColor("#1E293B"))
    p.setFont("Helvetica-Bold", 10)
    p.drawRightString(540, totals_box_y + 60, f"₹ {float(bill['total_amount']):,.2f}")
    p.drawRightString(540, totals_box_y + 38, f"₹ {float(bill['gst_amount']):,.2f}")
    
    p.setFillColor(colors.HexColor("#0F4C81"))
    p.setFont("Helvetica-Bold", 12)
    p.drawRightString(540, totals_box_y + 14, f"₹ {float(bill['final_amount']):,.2f}")

    # ----------------------------------------------------------------------
    # AUTHORIZATION AND CORPORATE GRATITUDE VALIDATION FOOTER
    # ----------------------------------------------------------------------
    p.setStrokeColor(colors.HexColor("#475569"))
    p.setLineWidth(1.5)
    p.line(40, 95, 180, 95)

    p.setFillColor(colors.HexColor("#1E293B"))
    p.setFont("Helvetica-Bold", 10)
    p.drawString(52, 80, "Authorized Signature")

    p.setFillColor(colors.HexColor("#64748b"))
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(40, 45, "Thank you for your business!")

    p.save()

    if os.path.exists(qr_path):
        os.remove(qr_path)

    pdf_buffer.seek(0)

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"invoice_{bill_id}.pdf",
        mimetype="application/pdf"
    )