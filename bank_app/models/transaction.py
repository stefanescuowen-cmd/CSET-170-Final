from . import db

class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer)
    recipient_id = db.Column(db.Integer)
    amount = db.Column(db.Float)
    type = db.Column(db.String(20))