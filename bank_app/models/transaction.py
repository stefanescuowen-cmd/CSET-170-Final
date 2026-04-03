from . import db
from datetime import datetime

class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)

    # Foreign keys
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # Relationships
    sender = db.relationship("User", foreign_keys=[sender_id], backref="sent_transactions")
    recipient = db.relationship("User", foreign_keys=[recipient_id], backref="received_transactions")

    # Core transaction data
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # "deposit" or "transfer"

    # Credit / Debit
    direction = db.Column(db.String(10), nullable=False)  # "credit" or "debit"

    # Extra info
    description = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Transaction {self.type} {self.direction} ${self.amount}>"