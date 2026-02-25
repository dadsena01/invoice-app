from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required
import datetime
from decimal import Decimal
from app.utils import generate_invoice_pdf
from app.models import Customer, InvoiceItem, Item, Invoice
from app.einvoice import get_arn

api = Blueprint("api", __name__)


@api.route("/customers", methods=["POST", "GET"])
@login_required
def create_customer():
    if request.method == "POST":
        data = request.get_json()
        customer = Customer.create(
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            address=data.get("address", " "),
        )
        return jsonify({"message": "Customer created", "id": customer.id}), 201
    elif request.method == "GET":
        customers = Customer.select().order_by(Customer.id.desc())
        data = [{"id": c.id, "name": c.name, "email": c.email} for c in customers]
        return jsonify(data), 200


@api.route("/items", methods=["GET"])
@login_required
def get_items():
    items = Item.select().order_by(Item.id.desc())
    return (
        jsonify([{"id": i.id, "name": i.name, "price": str(i.price)} for i in items]),
        200,
    )


@api.route("/items", methods=["POST"])
@login_required
def create_item():
    data = request.get_json()
    if not data.get("name") or not data.get("price"):
        return jsonify({"error": "Name and Price are required"}), 400

    item = Item.create(name=data["name"], price=data["price"])
    return jsonify({"id": item.id, "message": "Item created"}), 201


@api.route("/invoices", methods=["POST"])
@login_required
def create_invoice():
    data = request.get_json()
    customer = Customer.get_by_id(data["customer_id"])

    tax_type = data.get("tax_type", "GST")
    tax_rate = Decimal(str(data.get("tax_rate", 0)))

    invoice = Invoice.create(
        customer=customer,
        date=datetime.date.today(),
        tax_type=tax_type,
        tax_rate=tax_rate,
        total_amount=0,
        status="Draft",
    )

    subtotal = Decimal(0)

    for entry in data["items"]:
        item = Item.get_by_id(entry["item_id"])
        qty = int(entry["quantity"])

        line_total = item.price * qty

        InvoiceItem.create(
            invoice=invoice,
            item_name=item.name,
            item_price=item.price,
            quantity=qty,
            line_total=line_total,
        )
        subtotal += line_total

    tax_amount = subtotal * (tax_rate / Decimal(100))
    grand_total = subtotal + tax_amount

    invoice.total_amount = grand_total
    invoice.save()

    return (
        jsonify(
            {
                "invoice_id": invoice.id,
                "message": "Draft Invoice saved",
                "total": str(grand_total),
            }
        ),
        201,
    )


@api.route("/invoices/<int:id>/finalize", methods=["POST"])
@login_required
def finalize_invoice(id):
    invoice = Invoice.get_by_id(id)
    if invoice.status == "Finalized":
        return jsonify({"message": "Already finalized"}), 400

    new_arn = get_arn(invoice.id, "Admin")

    if new_arn:
        invoice.arn = new_arn
        invoice.status = "Finalized"
        invoice.save()
        return jsonify({"message": "Invoice Finalized", "arn": new_arn}), 200
    else:
        return jsonify({"error": "API failed to give ARN"}), 500


@api.route("/invoices/<int:id>", methods=["DELETE"])
@login_required
def delete_invoice(id):
    invoice = Invoice.get_by_id(id)
    query = InvoiceItem.delete().where(InvoiceItem.invoice == invoice)
    query.execute()

    invoice.delete_instance()

    return jsonify({"message": "Invoice deleted"}), 200


@api.route("/invoices/<int:id>/pdf", methods=["GET"])
@login_required
def download_invoice_pdf(id):
    invoice = Invoice.get_by_id(id)
    pdf_output = generate_invoice_pdf(invoice)

    return send_file(
        pdf_output,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"invoice_{id}.pdf",
    )


@api.route("/items/<int:id>", methods=["PUT"])
@login_required
def update_item(id):
    data = request.get_json()
    try:
        item = Item.get_by_id(id)
        item.name = data["name"]
        item.price = data["price"]
        item.save()
        return jsonify({"message": "Item updated"}), 200
    except Item.DoesNotExist:
        return jsonify({"error": "Item not found"}), 404


@api.route("/customers/<int:id>", methods=["PUT"])
@login_required
def update_customer(id):
    data = request.get_json()
    try:
        customer = Customer.get_by_id(id)
        customer.name = data["name"]
        customer.email = data["email"]
        customer.phone = data.get("phone", "")
        customer.address = data.get("address", "")
        customer.save()
        return jsonify({"message": "Customer updated successfully"}), 200
    except Customer.DoesNotExist:
        return jsonify({"error": "Customer not found"}), 404


@api.route("/customers/<int:id>", methods=["DELETE"])
@login_required
def delete_customer(id):
    customer = Customer.get_by_id(id)
    customer.delete_instance(recursive=True)
    return jsonify({"message": "Customer deleted"}), 200


@api.route("/items/<int:id>", methods=["DELETE"])
@login_required
def delete_item(id):
    item = Item.get_by_id(id)
    item.delete_instance()
    return jsonify({"message": "Item deleted"}), 200
