import os
import tempfile
from flask import Blueprint, send_file
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
from config import get_connection
import qrcode

invoice_bp = Blueprint('invoice_bp', __name__)

# ── Register a Unicode font that supports ₹ ──────────────────────────────────
# Try Windows fonts first, then Linux fallback
_FONT_CANDIDATES = [
    # Windows
    ("C:/Windows/Fonts/arial.ttf",        "C:/Windows/Fonts/arialbd.ttf",
     "C:/Windows/Fonts/ariali.ttf",       "C:/Windows/Fonts/arialbi.ttf"),
    # macOS
    ("/Library/Fonts/Arial.ttf",          "/Library/Fonts/Arial Bold.ttf",
     "/Library/Fonts/Arial Italic.ttf",   "/Library/Fonts/Arial Bold Italic.ttf"),
    # Linux
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"),
]

_BASE_FONT = "Helvetica"   # fallback if nothing found (₹ will still break)

for reg, bold, italic, bolditalic in _FONT_CANDIDATES:
    if os.path.exists(reg):
        try:
            pdfmetrics.registerFont(TTFont("InvFont",       reg))
            pdfmetrics.registerFont(TTFont("InvFont-Bold",  bold))
            pdfmetrics.registerFont(TTFont("InvFont-Italic",italic))
            _BASE_FONT = "InvFont"
            break
        except Exception:
            continue

_BOLD   = _BASE_FONT + "-Bold"   if _BASE_FONT != "Helvetica" else "Helvetica-Bold"
_ITALIC = _BASE_FONT + "-Italic" if _BASE_FONT != "Helvetica" else "Helvetica-Oblique"
_REG    = _BASE_FONT


@invoice_bp.route('/invoice/<int:bill_id>', methods=['GET'])
def generate_invoice(bill_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM bills WHERE bill_id = %s", (bill_id,))
    bill = cursor.fetchone()
    if not bill:
        return {"error": "Bill not found"}, 404

    cursor.execute("SELECT * FROM customers WHERE customer_id = %s", (bill['customer_id'],))
    customer = cursor.fetchone()

    # Strictly filtered to THIS bill only
    cursor.execute("""
        SELECT p.product_name, bi.quantity, bi.price, bi.subtotal
        FROM bill_items bi
        JOIN products p ON p.product_id = bi.product_id
        WHERE bi.bill_id = %s
    """, (bill_id,))
    items = cursor.fetchall()
    cursor.close()
    conn.close()

    # ── helpers ──────────────────────────────────────────────────────────────
    def v(val, fallback='—'):
        return str(val) if val not in (None, '', 'None') else fallback

    def rupee(val):
        try:
            return f"\u20b9{float(val):,.2f}"   # ₹ using unicode escape
        except Exception:
            return "\u20b90.00"

    # ── data ─────────────────────────────────────────────────────────────────
    cname        = v(customer.get('customer_name') if customer else None)
    cphone       = v(customer.get('phone')         if customer else None)
    cemail       = v(customer.get('email')         if customer else None)
    caddr        = v(customer.get('address')       if customer else None)
    cgst_no      = v(customer.get('gst_number')    if customer else None)

    bill_no      = v(bill.get('bill_id'))
    bill_date    = v(bill.get('bill_date') or bill.get('created_at'))
    due_date     = v(bill.get('due_date'))
    payment_mode = v(bill.get('payment_mode'), 'Cash')
    gst_rate     = float(bill.get('gst_rate') or 18)
    gst_type     = v(bill.get('gst_type'), 'exclusive').capitalize()
    total_amount = float(bill.get('total_amount') or 0)
    gst_amount   = float(bill.get('gst_amount')   or 0)
    final_amount = float(bill.get('final_amount') or 0)
    discount_amt = float(bill.get('discount_amt') or 0)
    taxable      = max(0.0, total_amount - discount_amt)
    half_gst     = gst_rate / 2
    notes        = v(bill.get('notes'), '')

    # ── colours — WHITE page only, no background fills ───────────────────────
    BLACK  = colors.HexColor("#111827")
    DARK   = colors.HexColor("#1F2937")
    MID    = colors.HexColor("#374151")
    MUTED  = colors.HexColor("#6B7280")
    LIGHT  = colors.HexColor("#9CA3AF")
    BORDER = colors.HexColor("#D1D5DB")
    ALTROW = colors.HexColor("#F9FAFB")
    RED    = colors.HexColor("#DC2626")
    WHITE  = colors.white

    # ── canvas ───────────────────────────────────────────────────────────────
    buf = BytesIO()
    c   = canvas.Canvas(buf)
    W, H, M = 595, 842, 40    # A4, margin

    def reg(size):  c.setFont(_REG,  size)
    def bold(size): c.setFont(_BOLD, size)
    def ital(size): c.setFont(_ITALIC, size)

    # ══════════════════════════════════════════════════════════════════════════
    # HEADER
    # ══════════════════════════════════════════════════════════════════════════
    # Company name — top left
    bold(14)
    c.setFillColor(BLACK)
    c.drawString(M, H - 36, "Inventory Billing System")
    reg(8.5)
    c.setFillColor(MUTED)
    c.drawString(M, H - 50, "Khopoli, Maharashtra, India")

    # "INVOICE" — top right
    bold(28)
    c.setFillColor(BLACK)
    c.drawRightString(W - M, H - 34, "INVOICE")
    reg(9)
    c.setFillColor(MUTED)
    c.drawRightString(W - M, H - 50, f"No. {bill_no}")

    # Divider
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(M, H - 60, W - M, H - 60)

    # ══════════════════════════════════════════════════════════════════════════
    # META ROW  (Date / Due Date / Payment / GST)
    # ══════════════════════════════════════════════════════════════════════════
    y = H - 76
    meta = [
        ("DATE",         bill_date),
        ("DUE DATE",     due_date),
        ("PAYMENT MODE", payment_mode),
        ("GST",          f"{gst_rate}% {gst_type}"),
    ]
    col_w = (W - M * 2) / 4
    for i, (lbl, val) in enumerate(meta):
        x = M + i * col_w
        bold(7)
        c.setFillColor(MUTED)
        c.drawString(x, y, lbl)
        reg(9)
        c.setFillColor(DARK)
        c.drawString(x, y - 13, val)

    y -= 32
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(M, y, W - M, y)

    # ══════════════════════════════════════════════════════════════════════════
    # BILL FROM  /  BILL TO
    # ══════════════════════════════════════════════════════════════════════════
    y -= 12
    half = (W - M * 2) / 2

    def addr_block(x, title, name, lines):
        cy = y
        bold(7)
        c.setFillColor(MUTED)
        c.drawString(x, cy, title)
        cy -= 14
        bold(10)
        c.setFillColor(BLACK)
        c.drawString(x, cy, name)
        cy -= 13
        reg(8.5)
        c.setFillColor(MID)
        for ln in lines:
            if ln and ln not in ('—', 'None'):
                c.drawString(x, cy, ln)
                cy -= 12
        return cy

    from_lines = ["Khopoli, Maharashtra", "India"]
    to_lines   = []
    if cphone != '—':  to_lines.append(f"Phone: {cphone}")
    if cemail != '—':  to_lines.append(f"Email: {cemail}")
    if caddr  != '—':  to_lines.append(f"Address: {caddr}")
    if cgst_no!= '—':  to_lines.append(f"GSTIN: {cgst_no}")

    b1 = addr_block(M,          "BILL FROM", "Inventory Billing System", from_lines)
    b2 = addr_block(M + half,   "BILL TO",   cname,                      to_lines)
    y  = min(b1, b2) - 16

    # QR code top-right (optional)
    try:
        qr_img  = qrcode.make(f"http://127.0.0.1:5000/invoice/{bill_id}")
        qr_path = os.path.join(tempfile.gettempdir(), f"qr_{bill_id}.png")
        qr_img.save(qr_path)
        c.drawImage(qr_path, W - M - 56, H - 170, width=56, height=56)
        if os.path.exists(qr_path):
            os.remove(qr_path)
    except Exception:
        pass

    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(M, y, W - M, y)
    y -= 2

    # ══════════════════════════════════════════════════════════════════════════
    # ITEMS TABLE
    # ══════════════════════════════════════════════════════════════════════════
    TBL_W = W - M * 2
    ROW_H = 26
    HDR_H = 24

    # Column positions
    XI = M           # Item name — left aligned
    XQ = M + 248     # Qty — centre
    XR = M + 338     # Rate — centre
    XT = M + 420     # Tax — centre
    XA = W - M       # Amount — right

    # Header — light gray fill
    c.setFillColor(colors.HexColor("#F3F4F6"))
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.4)
    c.rect(M, y - HDR_H, TBL_W, HDR_H, fill=1, stroke=1)

    bold(8)
    c.setFillColor(BLACK)
    c.drawString(XI + 8,        y - 16, "ITEM")
    c.drawCentredString(XQ + 22, y - 16, "QUANTITY")
    c.drawCentredString(XR + 22, y - 16, "RATE")
    c.drawCentredString(XT + 15, y - 16, "TAX")
    c.drawRightString(XA - 8,   y - 16, "AMOUNT")
    y -= HDR_H

    for idx, item in enumerate(items):
        if y < 160:
            ital(8)
            c.setFillColor(LIGHT)
            c.drawString(XI + 8, y - 14, "* Additional items — see full records.")
            y -= ROW_H
            break

        # Alternating row background
        c.setFillColor(WHITE if idx % 2 == 0 else ALTROW)
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.4)
        c.rect(M, y - ROW_H, TBL_W, ROW_H, fill=1, stroke=1)

        iprice = float(item['price'])
        iqty   = int(item['quantity'])
        isub   = float(item['subtotal'])

        reg(9)
        c.setFillColor(DARK)
        c.drawString(XI + 8,         y - 17, str(item['product_name']))
        c.drawCentredString(XQ + 22,  y - 17, str(iqty))
        c.setFillColor(MID)
        c.drawCentredString(XR + 22,  y - 17, rupee(iprice))
        c.drawCentredString(XT + 15,  y - 17, f"{gst_rate}%")
        bold(9)
        c.setFillColor(DARK)
        c.drawRightString(XA - 8,     y - 17, rupee(isub))

        y -= ROW_H

    # Bottom table line
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(M, y, M + TBL_W, y)

    # ══════════════════════════════════════════════════════════════════════════
    # TOTALS  — right side, notes on left
    # ══════════════════════════════════════════════════════════════════════════
    y   -= 14
    TX   = 320       # totals left edge
    ty   = y

    def trow(label, val, val_color=DARK, is_bold=False):
        nonlocal ty
        fn = bold if is_bold else reg
        fn(9)
        c.setFillColor(MUTED)
        c.drawString(TX, ty, label)
        c.setFillColor(val_color)
        c.drawRightString(W - M, ty, val)
        ty -= 16

    trow("Subtotal:",             rupee(total_amount))
    trow("Discount:",             f"- {rupee(discount_amt)}", RED)
    trow("Taxable Amount:",       rupee(taxable))
    trow(f"CGST ({half_gst}%):",  rupee(gst_amount / 2))
    trow(f"SGST ({half_gst}%):",  rupee(gst_amount / 2))

    # Divider
    ty -= 4
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(TX, ty, W - M, ty)
    ty -= 4

    # Grand Total — bold, larger, no background
    bold(12)
    c.setFillColor(BLACK)
    c.drawString(TX, ty - 16, "Total")
    c.drawRightString(W - M, ty - 16, rupee(final_amount))

    # Double underline for total
    c.setStrokeColor(BLACK)
    c.setLineWidth(1)
    c.line(TX, ty - 20, W - M, ty - 20)
    c.setLineWidth(0.4)
    c.line(TX, ty - 23, W - M, ty - 23)

    # Notes — left of totals block
    if notes and notes not in ('—', ''):
        bold(8.5)
        c.setFillColor(MID)
        c.drawString(M, y, "Terms & Conditions:")
        ny = y - 14
        reg(8.5)
        c.setFillColor(MUTED)
        line = ''
        for w in notes.split():
            test = (line + ' ' + w).strip()
            if c.stringWidth(test, _REG, 8.5) < 260:
                line = test
            else:
                c.drawString(M, ny, line); ny -= 12; line = w
        if line:
            c.drawString(M, ny, line)

    # ══════════════════════════════════════════════════════════════════════════
    # FOOTER
    # ══════════════════════════════════════════════════════════════════════════
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(M, 68, W - M, 68)

    # Signature line
    c.setStrokeColor(colors.HexColor("#9CA3AF"))
    c.setLineWidth(0.8)
    c.line(M, 55, M + 130, 55)
    bold(8.5)
    c.setFillColor(DARK)
    c.drawString(M, 42, "Authorized Signature")

    ital(8.5)
    c.setFillColor(MUTED)
    c.drawCentredString(W / 2, 42, "Thank you for your business!")

    reg(7.5)
    c.setFillColor(LIGHT)
    c.drawRightString(W - M, 42, "Generated by ERP System")

    # ── save ─────────────────────────────────────────────────────────────────
    c.save()
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name=f"invoice_{bill_id}.pdf",
        mimetype="application/pdf"
    )