# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Flask-based invoice management web application using Peewee ORM with SQLite, Flask-Login for session auth, WeasyPrint for PDF generation, and a Jinja2 template frontend.

## Running the App

```bash
# Install dependencies
pip install -r requirements.txt

# Seed the initial admin user (run once)
python seed.py

# Start development server
python run.py
```

The app runs on `http://localhost:5000` by default. Default credentials seeded: `admin@example.com` / `password123`.

## Environment Variables

Create a `.env` file with:

```
API_URL=<e-invoice API endpoint>
API_KEY=<API key>
API_SECRET=<API secret>
```

These are required for invoice finalization (`einvoice.py` calls the external ARN service).

## Architecture

### Blueprints

| Blueprint | Prefix | File | Purpose |
|-----------|--------|------|---------|
| `auth` | `/auth` | `auth.py` | Login/logout |
| `api` | `/api` | `routes.py` | JSON REST endpoints |
| `views` | `/` | `views.py` | HTML page rendering |

All `/api` and view routes (except `/`, `/login`) require `@login_required`.

### Data Models (`models.py`)

- `User` — app users (email/password, no hashing currently)
- `Customer` — invoice recipients
- `Item` — reusable product/service catalog
- `Invoice` — links to Customer, tracks status (`Draft` → `Finalized`), tax, ARN
- `InvoiceItem` — line items denormalized from Item at invoice creation time

SQLite database file: `invoice.db` (auto-created on first run via `initialize_db()`).

### Key Flows

**Invoice creation** (`POST /api/invoices`): accepts `customer_id`, `items[]` (item_id + quantity), `tax_type`, `tax_rate`. Line totals are calculated and tax is applied server-side; total stored on the Invoice record.

**Invoice finalization** (`POST /api/invoices/<id>/finalize`): calls external ARN API via `einvoice.py::get_arn()`, stores returned ARN, marks invoice `Finalized`.

**PDF download** (`GET /api/invoices/<id>/pdf`): generates PDF in-memory using WeasyPrint from an HTML template in `utils.py`.

### Frontend

Server-rendered Jinja2 templates in `app/templates/`. `base.html` is the layout base. Templates call the `/api` endpoints via `fetch` for mutations (create, update, delete, finalize), then redirect or update the DOM.

## API Testing

Bruno collection lives in `Bruno Api/`. Use [Bruno](https://www.usebruno.com/) to run/explore the API requests.
