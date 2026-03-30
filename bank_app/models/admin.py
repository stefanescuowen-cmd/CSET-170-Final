from main import db, User
from werkzeug.security import generate_password_hash

admin = User(
    username="admin",
    first_name="Admin",
    last_name="User",
    password=generate_password_hash("admin123"),
    approved=True,
    is_admin=True
)

db.session.add(admin)
db.session.commit()