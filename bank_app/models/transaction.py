from . import db
from datetime import datetime

class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    # Relationships
    sender = db.relationship("User", foreign_keys=[sender_id], backref="sent_transactions")
    recipient = db.relationship("User", foreign_keys=[recipient_id], backref="received_transactions")

    # Transaction details
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # e.g., "deposit" or "transfer"
    description = db.Column(db.String(200))  # optional note about transaction
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # automatic timestamp

    def __repr__(self):
        return f"<Transaction {self.type} ${self.amount} from {self.sender_id} to {self.recipient_id}>"