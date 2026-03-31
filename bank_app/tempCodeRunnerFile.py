sender.balance -= amount
        recipient.balance += amount
        db.session.commit()