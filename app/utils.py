from weasyprint import HTML
import io
from app.models import get_settings

def generate_invoice_pdf(invoice):
    settings = get_settings()
    subtotal = sum(item.line_total for item in invoice.items)
    tax_amount = invoice.total_amount - subtotal
    tax_label = f"{invoice.tax_type} ({invoice.tax_rate}%)"
    invoice_number = f"{settings.invoice_prefix}-{invoice.date.year}-{str(invoice.id).zfill(4)}"

    rows_html = ""
    for item in invoice.items:
        rows_html += f"""
        <tr>
            <td>{item.item_name}</td>
            <td>{item.quantity}</td>
            <td>₹{item.item_price}</td>
            <td>₹{item.line_total}</td>
        </tr>
        """

    seller_gstin = f"<p>GSTIN: {settings.gstin}</p>" if settings.gstin else ""
    seller_address = f"<p>{settings.address}</p>" if settings.address else ""
    customer_address = f"<p>{invoice.customer.address}</p>" if invoice.customer.address and invoice.customer.address.strip() else ""
    customer_gstin = f"<p>GSTIN: {invoice.customer.gstin}</p>" if invoice.customer.gstin else ""

    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; padding: 20px; }}
            .top {{ display: flex; justify-content: space-between; margin-bottom: 24px; }}
            .seller {{ font-size: 13px; }}
            .seller h2 {{ margin: 0 0 4px; font-size: 18px; }}
            .meta {{ text-align: right; font-size: 13px; color: #555; }}
            .meta h1 {{ margin: 0 0 4px; font-size: 22px; color: #111; }}
            .bill-row {{ display: flex; gap: 40px; margin-bottom: 20px; font-size: 13px; }}
            .bill-section h4 {{ margin: 0 0 4px; font-size: 11px; text-transform: uppercase; color: #888; }}
            .bill-section p {{ margin: 2px 0; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 13px; }}
            th {{ background: #f5f5f5; }}
            .total-block {{ margin-top: 16px; text-align: right; font-size: 13px; }}
            .total-block p {{ margin: 4px 0; color: #555; }}
            .total-block .grand {{ font-size: 16px; font-weight: bold; color: #111; border-top: 2px solid #333; padding-top: 6px; margin-top: 6px; }}
            .arn {{ margin-top: 16px; font-size: 11px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="top">
            <div class="seller">
                <h2>{settings.business_name}</h2>
                {seller_gstin}
                {seller_address}
            </div>
            <div class="meta">
                <h1>INVOICE</h1>
                <p><strong>{invoice_number}</strong></p>
                <p>Date: {invoice.date}</p>
                <p>Status: {invoice.status}</p>
            </div>
        </div>

        <div class="bill-row">
            <div class="bill-section">
                <h4>Bill To</h4>
                <p><strong>{invoice.customer.name}</strong></p>
                <p>{invoice.customer.email}</p>
                {customer_address}
                {customer_gstin}
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Item</th>
                    <th>Qty</th>
                    <th>Unit Price</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>

        <div class="total-block">
            <p>Subtotal: ₹{subtotal}</p>
            <p>{tax_label}: ₹{round(tax_amount, 2)}</p>
            <p class="grand">TOTAL: ₹{invoice.total_amount}</p>
        </div>

        <div class="arn">ARN: {invoice.arn if invoice.arn else 'Pending'}</div>
        {f'<div style="margin-top:16px; font-size:12px; color:#555; border-top:1px solid #eee; padding-top:10px;"><strong>Notes:</strong> {invoice.notes}</div>' if invoice.notes else ""}
    </body>
    </html>
    """

    pdf_file = io.BytesIO()
    HTML(string=html_content).write_pdf(pdf_file)
    pdf_file.seek(0)
    return pdf_file