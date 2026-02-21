from werkzeug.security import generate_password_hash
from app.models import initialize_db, User

initialize_db()

try:
    User.create(name="Admin", email="admin@example.com", password=generate_password_hash("password123"))
    print("User created")
except:
    print("User already exists")