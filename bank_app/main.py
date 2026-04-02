from flask import Flask, render_template, request, redirect, session, flash, get_flashed_messages
from functools import wraps
from config import Config
from models import db
from models.user import User
from models.transaction import Transaction
from werkzeug.security import generate_password_hash, check_password_hash
import random
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
# Authentication helpers
# ------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "error")
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)

# --------------
# Register Route
# --------------
@app.route("/register", methods=["GET", "POST"])
def register():
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

        return "Account created. Waiting for admin approval."

    return render_template("register.html")

# ----------- 
# Login Route
# -----------

@app.route("/login", methods=["GET", "POST"])
def login():
    # Redirect logged-in users to dashboard
    if "user_id" in session:
        return redirect("/dashboard")

    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()

        # Invalid username or password
        if not user or not check_password_hash(user.password, request.form["password"]):
            flash("Invalid credentials", "error")
            return redirect("/login")

        # Block login if not approved (non-admin users)
        if not user.approved and not user.is_admin:
            flash("Waiting for admin approval", "info")
            return redirect("/login")

        # Success: log in
        session["user_id"] = user.id
        session["is_admin"] = user.is_admin
        flash(f"Welcome, {user.first_name}!", "success")
        return redirect("/dashboard")

    return render_template("login.html")

# ------------
# Logout Route
# ------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect("/login")

# ----------------
# Admin Page Route
# ----------------
@app.route("/admin")
def admin_page():
    if not session.get("is_admin"):
        return "Unauthorized"

    pending_users = User.query.filter_by(approved=False).all()
    all_users = User.query.all()

    return render_template("admin.html", pending_users=pending_users, all_users=all_users)

# ------------------
# Approve User Route
# ------------------
@app.route("/approve/<int:user_id>")
def approve(user_id):
    if not session.get("is_admin"):
        flash("Unauthorized access", "error")
        return redirect("/login")

    user = User.query.get(user_id)
    if not user:
        flash("User not found", "error")
        return redirect("/admin")

    user.approved = True
    user.account_number = generate_account_number()

    db.session.commit()
    flash(f"User {user.username} approved successfully!", "success")
    return redirect("/admin")

# -----------------
# Delete User Route
# -----------------

@app.route("/delete/<int:user_id>")
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

# -----------------------
# View User Details Route
# -----------------------

@app.route("/user/<int:user_id>")
def view_user(user_id):
    if not session.get("is_admin"):
        return "Unauthorized"

    user = User.query.get(user_id)
    return render_template("user_detail.html", user=user)

# ---------------
# Statement Route
# ---------------

@app.route("/statement")
def statement():
    if "user_id" not in session or session.get("is_admin"):
        flash("Unauthorized", "error")
        return redirect("/login")

    user = User.query.get(session["user_id"])

    transactions = Transaction.query.filter(
        (Transaction.sender_id == user.id) |
        (Transaction.recipient_id == user.id)
    ).all()

    return render_template("statement.html", transactions=transactions, user=user)

# -------------
# Deposit Route
# -------------

@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    user = get_current_user()
    if request.method == "POST":
        try:
            amount = float(request.form["amount"])
            if amount <= 0: raise ValueError
            
            user.balance += amount
            db.session.add(Transaction(sender_id=user.id, recipient_id=user.id, amount=amount, type="deposit"))
            db.session.commit()
            flash(f"${amount:.2f} deposited!", "success")
            return redirect("/dashboard")
        except ValueError:
            flash("Invalid positive amount required", "error")
            
    return render_template("deposit.html")

@app.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():
    sender = get_current_user()
    if request.method == "POST":
        recipient = User.query.filter_by(account_number=request.form.get("account_number")).first()
        amount = float(request.form.get("amount", 0))

        if not recipient or recipient.id == sender.id:
            flash("Invalid recipient", "error")
        elif sender.balance < amount:
            flash("Insufficient funds", "error")
        else:
            sender.balance -= amount
            recipient.balance += amount
            db.session.add(Transaction(sender_id=sender.id, recipient_id=recipient.id, amount=amount, type="transfer"))
            db.session.commit()
            flash("Transfer successful!", "success")
            return redirect("/dashboard")

    return render_template("transfer.html")

# ---------------------------
# Dashboard Route
# --------------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    # Prevent the admin from using user dashboard
    if session.get("is_admin"):
        return redirect("/admin")

    user = User.query.get(session["user_id"])
    return render_template("dashboard.html", user=user)

# -------------------------
# Run the app / Admin Setup
# -------------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # create tables if they don't exist

        # Check if admin exists
        admin_user = User.query.filter_by(username="admin").first()

        if not admin_user:
            # Create default admin
            admin_user = User(
                username="admin",
                first_name="Admin",
                last_name="User",
                ssn="000-00-0000",
                address="Bank HQ",
                phone="1234567890",
                password=generate_password_hash("admin123"),  # password to match your login
                approved=True,
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin created: username=admin, password=admin123")
            
            admin_user.account_number = None
            admin_user.balance = 0

            db.session.add(admin_user)
            db.session.commit()

        else:
            # Optional: ensure admin has correct password and flags (dev convenience)
            admin_user.password = generate_password_hash("admin123")
            admin_user.approved = True
            admin_user.is_admin = True
            db.session.commit()
            print("Admin already exists — password reset to 'admin123' for consistency")

            admin_user.account_number = None
            admin_user.balance = 0

            db.session.commit()

    app.run(debug=True)