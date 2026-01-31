from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from app.firestore_service import list_menu_items, add_menu_item
from werkzeug.security import generate_password_hash, check_password_hash

from app.config import Config
from app.models import db, User

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    if not app.testing:
        with app.app_context():
            db.create_all()

    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            if not email or not password:
                flash("Email and password are required.", "error")
                return redirect(url_for("register"))

            #check if the user already exists in the database
            existing = User.query.filter_by(email=email).first()
            if existing:
                flash("That email is already registered. Please log in.", "error")
                return redirect(url_for("login"))

            password_hash = generate_password_hash(password)

            user = User(email=email, password_hash=password_hash)
            db.session.add(user)
            db.session.commit()

            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            if not email or not password:
                flash("Email and password are required.", "error")
                return redirect(url_for("login"))

            user = User.query.filter_by(email=email).first()
            if not user or not check_password_hash(user.password_hash, password):
                flash("Invalid email or password.", "error")
                return redirect(url_for("login"))

            #login session
            session["user_id"] = user.id
            session["user_email"] = user.email
            session["user_role"] = user.role

            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard"))

        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("Logged out.", "success")
        return redirect(url_for("home"))

    @app.route("/dashboard")
    def dashboard():
        #simple protected route
        if "user_id" not in session:
            flash("Please log in to access the dashboard.", "error")
            return redirect(url_for("login"))

        return render_template("dashboard.html", email=session.get("user_email"))
    
    @app.route("/menu")
    def menu():
        items = list_menu_items()
        return render_template("menu.html", items=items)

    @app.route("/api/menu", methods=["GET"])
    def api_menu():
        return jsonify(list_menu_items())

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)