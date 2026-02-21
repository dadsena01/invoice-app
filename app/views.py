from peewee import fn
from app.models import Customer, Invoice, Item, InvoiceItem, get_settings
from flask import Blueprint, render_template, redirect
from flask_login import login_required, current_user

views = Blueprint('views', __name__)

@views.route('/')
def home():
    if current_user.is_authenticated:
        return redirect('/dashboard')
    return render_template('landing.html')

@views.route('/dashboard')
@login_required
def dashboard():
    total_invoices = Invoice.select().count()
    draft_count = Invoice.select().where(Invoice.status == 'Draft').count()
    finalized_count = Invoice.select().where(Invoice.status == 'Finalized').count()
    total_customers = Customer.select().count()
    total_revenue = Invoice.select(fn.SUM(Invoice.total_amount)).where(Invoice.status == 'Finalized').scalar() or 0
    recent_invoices = Invoice.select().join(Customer).order_by(Invoice.id.desc()).limit(5)
    return render_template('dashboard.html',
        total_invoices=total_invoices,
        draft_count=draft_count,
        finalized_count=finalized_count,
        total_customers=total_customers,
        total_revenue=total_revenue,
        recent_invoices=recent_invoices,
    )

@views.route('/login')
def login_page():
    return render_template('login.html')

@views.route('/customers')
@login_required
def customers_page():
   all_customers = Customer.select().order_by(Customer.id.desc())
   return render_template('customers.html', customers=all_customers)

@views.route('/invoices')
@login_required
def invoices_page():
    from flask import request as req
    page = max(1, int(req.args.get('page', 1)))
    per_page = 20
    total = Invoice.select().count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    all_invoices = Invoice.select().join(Customer).order_by(Invoice.id.desc()).paginate(page, per_page)
    return render_template('invoices.html', invoices=all_invoices, page=page, total_pages=total_pages)

@views.route('/invoices/<int:id>')
@login_required
def invoice_detail(id):
    invoice = Invoice.get_by_id(id)
    subtotal = sum(item.line_total for item in invoice.items)
    tax_amount = invoice.total_amount - subtotal
    return render_template('invoice_detail.html', invoice=invoice, subtotal=subtotal, tax_amount=tax_amount)

@views.route('/invoices/new')
@login_required
def new_invoice_page():
    customers = Customer.select().order_by(Customer.id.desc())
    items = Item.select().order_by(Item.id.desc())
    return render_template('create_invoice.html', customers=customers, items=items)

@views.route('/items')
@login_required
def items_page():
    items = Item.select().order_by(Item.id.desc())
    return render_template('items.html', items=items)

@views.route('/invoices/<int:id>/duplicate')
@login_required
def duplicate_invoice(id):
    invoice = Invoice.get_by_id(id)
    customers = Customer.select().order_by(Customer.id.desc())
    items = Item.select().order_by(Item.id.desc())
    return render_template('create_invoice.html', customers=customers, items=items,
                           prefill_customer_id=invoice.customer_id,
                           prefill_tax_type=invoice.tax_type,
                           prefill_tax_rate=invoice.tax_rate,
                           prefill_items=list(invoice.items))

@views.route('/invoices/<int:id>/edit')
@login_required
def edit_invoice_page(id):
    invoice = Invoice.get_by_id(id)
    if invoice.status == 'Finalized':
        return redirect(f'/invoices/{id}')
    customers = Customer.select().order_by(Customer.id.desc())
    items = Item.select().order_by(Item.id.desc())
    return render_template('edit_invoice.html', invoice=invoice, customers=customers, items=items)

@views.route('/settings')
@login_required
def settings_page():
    s = get_settings()
    return render_template('settings.html', settings=s)

@views.route('/customers/<int:id>/edit')
@login_required
def edit_customer_page(id):
    customer = Customer.get_by_id(id)
    return render_template('edit_customer.html', customer=customer)

@views.route('/items/<int:id>/edit')
@login_required
def edit_item_page(id):
    item = Item.get_by_id(id)
    return render_template('edit_item.html', item=item)