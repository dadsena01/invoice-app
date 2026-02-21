# Invoice App — Improvement Plan

Based on full codebase review and live end-to-end testing.

---

## 🔴 Critical Fixes (Security)

### 1. Plain-text password storage
**File:** `app/auth.py:15`, `app/models.py`
- Passwords are stored and compared as raw strings
- Fix: hash with `werkzeug.security.generate_password_hash` on save, `check_password_hash` on login
- Also update `seed.py` to hash the default password

### 2. Hardcoded weak SECRET_KEY
**File:** `app/__init__.py:13`
- `SECRET_KEY = "blank"` — sessions can be forged
- Fix: read from `.env` via `os.getenv("SECRET_KEY")`, throw on missing

### 3. No CSRF protection
- All state-changing API endpoints (`POST /api/invoices`, `DELETE`, etc.) accept requests from any origin
- Fix: add `flask-wtf` CSRF or validate `Origin`/`Referer` header on non-GET requests

---

## 🟠 Bugs

### 4. Phone stored as IntegerField
**File:** `app/models.py:19`
- `IntegerField` silently drops leading zeros, rejects `+91` prefix, fails on 11-digit numbers
- Fix: change to `CharField(max_length=15)`

### 5. Customer address missing from "New Customer" modal
**File:** `app/templates/customers.html:52-76`
- Address field exists in the `Customer` model and in `edit_customer.html` but not in the create modal
- Fix: add `<textarea>` for address in the create modal form

### 6. `finalize` uses `confirm()` dialog — blocks automation and UX
**File:** `app/templates/invoices.html:99`
- Native `confirm()` blocks agent-browser and is inconsistent with the rest of the UI (which uses inline modals)
- Fix: replace with a small inline confirmation UI or a custom modal (same pattern as delete on customers)

### 7. Status column conflates ARN with status badge
**File:** `app/templates/invoices.html:49-58`
- Finalized invoices show the raw ARN string as the status badge — truncated and unreadable
- Fix: show a green "Finalized" badge, put ARN in a separate column or tooltip

### 8. Finalized invoices can still be deleted
**File:** `app/templates/invoices.html:84-88`, `app/routes.py:113`
- No guard prevents deleting a finalized (ARN-issued) invoice, which creates a compliance gap
- Fix: check `invoice.status == 'Finalized'` in the delete route and return 400; hide the delete button on the frontend

### 9. macOS port 5000 conflict
**File:** `run.py`
- macOS AirPlay occupies `localhost:5000` on IPv6; Flask only binds `127.0.0.1` (IPv4)
- Fix: `app.run(host="127.0.0.1", port=5001, debug=True)` and document in README/CLAUDE.md

### 10. Customer address not shown in PDF
**File:** `app/utils.py:38-45`
- `Customer.address` is in the model and collected on edit, but the PDF template omits it
- Fix: add address line under customer email in the PDF Bill To section

---

## 🟡 Features

### 11. Dashboard (home page after login)
**File:** `app/views.py:9` — currently redirects straight to `/customers`
- Show: total invoices, total revenue, draft vs finalized count, recent 5 invoices
- Single query with `Invoice.select(fn.COUNT, fn.SUM).group_by(Invoice.status)`

### 12. Invoice detail / view page
- No way to see line items without downloading the PDF
- Add `GET /invoices/<id>` view that renders a read-only HTML version of the invoice

### 13. Edit Draft invoice
- After creation, a Draft invoice cannot be modified — items or customer can't be changed
- Add `GET /invoices/<id>/edit` view and `PUT /api/invoices/<id>` endpoint
- Only allow editing when `status == 'Draft'`

### 14. Search & filter on list pages
- Invoices: filter by status (Draft/Finalized), date range, customer
- Customers: search by name/email
- Items: search by name
- All can be done client-side with a simple JS filter on the rendered table (no backend change needed)

### 15. Business / Company profile
- PDF currently has no seller info — no business name, GSTIN, or address on the invoice
- Add a `Settings` model (single-row) with: business name, GSTIN, address, logo URL
- Render in PDF header and expose a `/settings` page for editing

### 16. GSTIN field on Customer
- Required for B2B GST compliance
- Add `gstin = CharField(null=True)` to `Customer` model
- Show on customer form and in invoice PDF

### 17. Tax type as dropdown, not free text
**File:** `app/templates/create_invoice.html:27`
- Tax type is a free `<input type="text">` — user can type anything
- Fix: replace with `<select>` with options: GST, IGST, CGST+SGST
- For CGST+SGST: split the rate in half and show two lines in the PDF

### 18. Custom invoice number format
- Currently just the raw DB integer `#1`, `#2`
- Add `invoice_prefix` setting (e.g. `INV`) and format as `INV-2026-0001`
- Stored in Settings (see #15)

### 19. Delete customer / delete item
- No delete buttons exist on customers or items pages
- Add `DELETE /api/customers/<id>` and `DELETE /api/items/<id>` routes
- Guard: prevent deleting a customer who has invoices; prevent deleting an item (denormalized data is already safe)

### 20. Notes / payment terms on invoice
- Add `notes = TextField(null=True)` to `Invoice` model
- Render as a textarea on the create form (e.g. "Payment due in 30 days", bank details)
- Include in PDF footer

### 21. Duplicate invoice
- "Copy" button on a finalized invoice to pre-fill a new Draft with the same customer and items
- One new view `GET /invoices/<id>/duplicate` that renders `create_invoice.html` with pre-selected values

### 22. Pagination
- All list pages load all records with no limit
- Add simple `page` query param + `LIMIT/OFFSET` in Peewee queries
- Show 20 records per page with Prev/Next links

---

## Priority Order

| Priority | Item |
|----------|------|
| P0 — Do immediately | #1 Password hashing, #2 SECRET_KEY from env |
| P1 — Before any real use | #4 Phone CharField, #5 Address in modal, #8 Protect finalized invoices, #10 Address in PDF |
| P2 — Core UX gaps | #11 Dashboard, #12 Invoice detail, #13 Edit draft, #14 Search/filter |
| P3 — Compliance | #15 Business profile, #16 GSTIN, #17 Tax dropdown, #18 Invoice number format |
| P4 — Nice to have | #19 Delete customer/item, #20 Notes, #21 Duplicate, #22 Pagination |
