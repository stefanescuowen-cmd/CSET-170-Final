from flask import Flask, render_template, request, redirect, session, flash, get_flashed_messages
from config import Config
from models import db
from models.user import User
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
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()

        # Check if user exists
        if not user:
            return "Invalid credentials"

        # Check password hash
        if not check_password_hash(user.password, request.form["password"]):
            return "Invalid credentials"

        # Only block approval for non-admin users
        if not user.approved and not user.is_admin:
            return "Waiting for admin approval"

        # Success: log in
        session["user_id"] = user.id
        session["is_admin"] = user.is_admin

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

    users = User.query.filter_by(approved=False).all()
    return render_template("admin.html", users=users)

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

# -------------
# Deposit Route
# -------------
@app.route("/deposit", methods=["POST"])
def deposit():
    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])

    try:
        amount = float(request.form["amount"])
    except ValueError:
        flash("Invalid amount", "error")
        return redirect("/dashboard")

    if amount <= 0:
        flash("Amount must be positive", "error")
        return redirect("/dashboard")

    user.balance += amount
    db.session.commit()

    flash(f"${amount:.2f} deposited successfully!", "success")
    return redirect("/dashboard")

# --------------
# Transfer Route
# --------------
@app.route("/transfer", methods=["POST"])
def transfer():
    if "user_id" not in session:
        return redirect("/login")

    sender = User.query.get(session["user_id"])
    recipient_account = request.form.get("account_number")

    try:
        amount = float(request.form.get("amount"))
    except ValueError:
        flash("Invalid amount", "error")
        return redirect("/dashboard")

    if amount <= 0:
        flash("Amount must be positive", "error")
        return redirect("/dashboard")

    recipient = User.query.filter_by(account_number=recipient_account).first()
    if not recipient:
        flash("Recipient not found", "error")
        return redirect("/dashboard")

    if recipient.id == sender.id:
        flash("You cannot transfer money to yourself.", "error")
        return redirect("/dashboard")

    if sender.balance < amount:
        flash("Insufficient funds", "error")
        return redirect("/dashboard")

    sender.balance -= amount
    recipient.balance += amount
    db.session.commit()

    flash(f"Transferred ${amount:.2f} to {recipient.username} successfully!", "success")
    return redirect("/dashboard")

# ---------------------------
# Dashboard Route
# ---------------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])
    return render_template("dashboard.html", user=user)

# -----------
# Run the app
# -----------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # create tables if they don't exist

        # Create default admin if it doesn't exist
        admin_user = User.query.filter_by(username="admin").first()
        if not admin_user:
            admin = User(
                username="admin",
                first_name="Admin",
                last_name="User",
                ssn="000-00-0000",
                address="Bank HQ",
                phone="1234567890",
                password=generate_password_hash("admin123"),  # ensure password matches login
                approved=True,
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: username=admin, password=admin123")

    app.run(debug=True)