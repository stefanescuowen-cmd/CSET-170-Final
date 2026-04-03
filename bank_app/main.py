from flask import Flask, render_template, request, redirect, session, flash
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import random

from models import db
from models.user import User
from models.transaction import Transaction
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# ------------------------
# Account Number Generator
# ------------------------
def generate_account_number():
    while True:
        number = str(random.randint(10000000, 99999999))
        if not User.query.filter_by(account_number=number).first():
            return number

# ------------------------
# Authentication Helpers
# ------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in.", "error")
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None

    user = User.query.get(user_id)
    if not user:
        session.clear()
        return None
    return user

# -----------------
# Routes
# -----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect("/dashboard")

    if request.method == "POST":
        hashed_password = generate_password_hash(request.form["password"])
        user = User(
            username=request.form["username"],
            first_name=request.form["first_name"],
            last_name=request.form["last_name"],
            ssn=request.form["ssn"],
            address=request.form["address"],
            phone=request.form["phone"],
            password=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash("Account created. Waiting for admin approval.", "success")
        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect("/dashboard")

    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if not user or not check_password_hash(user.password, request.form["password"]):
            flash("Invalid credentials", "error")
            return redirect("/login")

        if not user.approved and not user.is_admin:
            flash("Waiting for admin approval", "info")
            return redirect("/login")

        session["user_id"] = user.id
        session["is_admin"] = user.is_admin
        flash(f"Welcome, {user.first_name}!", "success")
        return redirect("/dashboard")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect("/login")

@app.route("/admin")
@login_required
def admin_page():
    if not session.get("is_admin"):
        return "Unauthorized"

    pending_users = User.query.filter_by(approved=False).all()
    all_users = User.query.all()
    return render_template("admin.html", pending_users=pending_users, all_users=all_users)

@app.route("/approve/<int:user_id>")
@login_required
def approve(user_id):
    if not session.get("is_admin"):
        return redirect("/login")

    user = User.query.get(user_id)
    if not user:
        flash("User not found", "error")
        return redirect("/admin")

    user.approved = True
    user.account_number = generate_account_number()
    db.session.commit()
    flash(f"{user.username} approved!", "success")
    return redirect("/admin")

@app.route("/delete/<int:user_id>")
@login_required
def delete_user(user_id):
    if not session.get("is_admin"):
        return "Unauthorized"

    user = User.query.get(user_id)
    if user and not user.is_admin:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted", "success")
    else:
        flash("Cannot delete admin", "error")
    return redirect("/admin")

@app.route("/statement")
@login_required
def statement():
    if session.get("is_admin"):
        return redirect("/admin")

    user = get_current_user()
    if not user:
        flash("Session expired. Please log in again.", "error")
        return redirect("/logout")

    transactions = Transaction.query.filter(
        (Transaction.sender_id == user.id) |
        (Transaction.recipient_id == user.id)
    ).order_by(Transaction.timestamp.desc()).all()

    return render_template("statement.html", transactions=transactions, user=user)

@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    if session.get("is_admin"):
        return redirect("/admin")

    user = get_current_user()
    if not user:
        flash("Session expired. Please log in again.", "error")
        return redirect("/logout")

    if request.method == "POST":
        card_number = request.form.get("card_number")
        try:
            amount = float(request.form["amount"])
        except:
            flash("Invalid amount", "error")
            return redirect("/deposit")

        if amount <= 0:
            flash("Amount must be positive", "error")
            return redirect("/deposit")

        user.balance += amount

        txn = Transaction(
            sender_id=user.id,
            recipient_id=user.id,
            amount=amount,
            type="deposit",
            direction="credit",
            description=f"Deposit via card ending {card_number[-4:]}"
        )

        db.session.add(txn)
        db.session.commit()
        flash(f"${amount:.2f} deposited!", "success")
        return redirect("/dashboard")

    return render_template("deposit.html")

@app.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():
    if session.get("is_admin"):
        return redirect("/admin")

    sender = get_current_user()
    if not sender:
        flash("Session expired. Please log in again.", "error")
        return redirect("/logout")

    if request.method == "POST":
        account_number = request.form.get("account_number")
        try:
            amount = float(request.form.get("amount"))
        except:
            flash("Invalid amount", "error")
            return redirect("/transfer")

        if amount <= 0:
            flash("Amount must be positive", "error")
            return redirect("/transfer")

        recipient = User.query.filter_by(account_number=account_number).first()
        if not recipient:
            flash("Recipient not found", "error")
            return redirect("/transfer")

        if recipient.id == sender.id:
            flash("Cannot send to yourself", "error")
            return redirect("/transfer")

        if sender.balance < amount:
            flash("Insufficient funds", "error")
            return redirect("/transfer")

        sender.balance -= amount
        recipient.balance += amount

        txn_out = Transaction(
            sender_id=sender.id,
            recipient_id=recipient.id,
            amount=amount,
            type="transfer",
            direction="debit",
            description=f"Sent to {recipient.username}"
        )
        txn_in = Transaction(
            sender_id=sender.id,
            recipient_id=recipient.id,
            amount=amount,
            type="transfer",
            direction="credit",
            description=f"Received from {sender.username}"
        )

        db.session.add(txn_out)
        db.session.add(txn_in)
        db.session.commit()
        flash(f"Transferred ${amount:.2f} to {recipient.username}", "success")
        return redirect("/dashboard")

    return render_template("transfer.html")

@app.route("/dashboard")
@login_required
def dashboard():
    if session.get("is_admin"):
        return redirect("/admin")

    user = get_current_user()
    if not user:
        flash("Session expired. Please log in again.", "error")
        return redirect("/logout")

    return render_template("dashboard.html", user=user)

@app.route("/change-password", methods=["POST"])
@login_required
def change_password():
    user = get_current_user()
    if not user:
        return redirect("/logout")

    current = request.form.get("current_password")
    new = request.form.get("new_password")

    if not check_password_hash(user.password, current):
        flash("Current password is incorrect", "error")
        return redirect("/dashboard")

    user.password = generate_password_hash(new)
    db.session.commit()
    flash("Password updated successfully", "success")
    return redirect("/dashboard")

# -------------------------
# Run the app / Admin Setup
# -------------------------
if __name__ == "__main__":
    with app.app_context():
        # Persistent DB file (must be set in Config)
        db.create_all()

        # Admin check
        if not User.query.filter_by(username="admin").first():
            admin_user = User(
                username="admin",
                first_name="Admin",
                last_name="User",
                ssn="000-00-0000",
                address="Bank HQ",
                phone="1234567890",
                password=generate_password_hash("admin123"),
                approved=True,
                is_admin=True,
                balance=0,
                account_number=None
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Admin created: username=admin, password=admin123")

    app.run(debug=True)