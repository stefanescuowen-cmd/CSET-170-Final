from . import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    ssn = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(200), nullable=False)

    approved = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

    account_number = db.Column(db.String(20), unique=True)
    balance = db.Column(db.Float, default=0.0)