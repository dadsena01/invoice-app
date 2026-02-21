from peewee import *
import datetime
from flask_login import UserMixin

db = SqliteDatabase("invoice.db")

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel, UserMixin):
    email = CharField(unique=True)
    password = CharField()
    name = CharField()

class Customer(BaseModel):
    name = CharField()
    email = CharField(unique=True)
    phone = CharField(max_length=15)
    address = TextField()
    gstin = CharField(max_length=15, null=True)


class Settings(BaseModel):
    business_name = CharField(default="My Business")
    gstin = CharField(max_length=15, null=True)
    address = TextField(null=True)
    invoice_prefix = CharField(max_length=10, default="INV")


class Item(BaseModel):
    name = CharField()
    price = DecimalField()


class Invoice(BaseModel):
    customer = ForeignKeyField(Customer, backref="invoices")
    date = DateField(default=datetime.date.today)
    total_amount = DecimalField(default=0.0)
    arn = CharField(null=True)
    status = CharField(default='Draft')
    tax_type = CharField(default="GST")
    tax_rate = DecimalField(default=0.0)
    notes = TextField(null=True)

class InvoiceItem(BaseModel):
    invoice = ForeignKeyField(Invoice, backref='items')
    item_name = CharField()    
    item_price = DecimalField()
    quantity = IntegerField()
    line_total = DecimalField()

def _migrate(migrations):
    for sql in migrations:
        try:
            db.execute_sql(sql)
        except Exception:
            pass  # column already exists

def initialize_db():
    db.connect()
    db.create_tables([User, Customer, Item, Invoice, InvoiceItem, Settings], safe=True)
    _migrate([
        "ALTER TABLE customer ADD COLUMN gstin VARCHAR(15)",
        "ALTER TABLE invoice ADD COLUMN notes TEXT",
    ])
    if not Settings.select().exists():
        Settings.create()
    db.close()

def get_settings():
    return Settings.get_by_id(1)

