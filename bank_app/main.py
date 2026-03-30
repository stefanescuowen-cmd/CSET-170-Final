from flask import Flask, render_template, request, redirect, session
from config import Config
from models import db
from models.user import User
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

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

        if user and check_password_hash(user.password, request.form["password"]):

            if not user.approved:
                return "Waiting for admin approval"

            session["user_id"] = user.id
            session["is_admin"] = user.is_admin

            return redirect("/dashboard")

        return "Invalid credentials"

    return render_template("login.html")

# ---------------------------
# Dashboard Route (Temporary)
# ---------------------------

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])
    return f"Welcome {user.first_name}, Balance: {user.balance}"

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)