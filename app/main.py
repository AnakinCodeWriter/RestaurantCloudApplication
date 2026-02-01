from dotenv import load_dotenv
load_dotenv()

import os, json
from google.cloud import pubsub_v1

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from app.firestore_service import list_menu_items, add_menu_item, get_menu_item
from werkzeug.security import generate_password_hash, check_password_hash

from app.config import Config
from app.models import db, User, Order, OrderItem

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

            user = User(email=email, password_hash=password_hash, role="customer")
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
    
    @app.route("/cart/add/<item_id>", methods=["POST"])
    def cart_add(item_id):
        item = get_menu_item(item_id)
        if not item:
            flash("Menu item not found.", "error")
            return redirect(url_for("menu"))
        
        cart = session.get("cart", {})
        cart[item_id] = cart.get(item_id, 0) + 1
        session["cart"] = cart

        flash(f"Added {item['name']} to cart.", "success")
        return redirect(url_for("menu"))

    @app.route("/cart")
    def cart_view():
        cart = session.get("cart", {})
        detailed = []
        total = 0.0

        for item_id, qty in cart.items():
            item = get_menu_item(item_id)
            if item:
                line_total = float(item["price"]) * qty
                total += line_total
                detailed.append({
                    "id": item_id,
                    "name": item["name"],
                    "price": float(item["price"]),
                    "quantity": qty,
                    "line_total": line_total
                })

        return render_template("cart.html", items=detailed, total=total)
    
    @app.route("/checkout", methods=["POST"])
    def checkout():
        if "user_id" not in session:
            flash("Please log in to checkout.", "error")
            return redirect(url_for("login"))

        cart = session.get("cart", {})
        if not cart:
            flash("Your cart is empty.", "error")
            return redirect(url_for("menu"))

        #building order items from the firestore database
        order_items = []
        total = 0.0

        for item_id, qty in cart.items():
            item = get_menu_item(item_id)
            if not item:
                continue
            price = float(item["price"])
            total += price * qty
            order_items.append((item_id, item["name"], price, qty))

        if not order_items:
            flash("Could not checkout because menu items were missing.", "error")
            return redirect(url_for("cart_view"))

        #writing to sql
        order = Order(user_id=session["user_id"], total=total, status="created")
        db.session.add(order)
        db.session.flush()  # get order.id before commit

        for item_id, name, price, qty in order_items:
            db.session.add(OrderItem(
                order_id=order.id,
                menu_item_id=item_id,
                name=name,
                price=price,
                quantity=qty
            ))

        db.session.commit()

        topic_name = os.environ.get("PUBSUB_TOPIC", "order-created")
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")  # set automatically on GCP
        if project_id:
            publisher = pubsub_v1.PublisherClient()
            topic_path = publisher.topic_path(project_id, topic_name)

            payload = {
                "order_id": order.id,
                "user_email": session.get("user_email"),
                "total": total
            }
            publisher.publish(topic_path, json.dumps(payload).encode("utf-8"))

        #clears the cart
        session["cart"] = {}

        flash(f"Order placed! Order #{order.id}", "success")
        return redirect(url_for("orders"))
    
    @app.route("/orders")
    def orders():
        if "user_id" not in session:
            flash("Please log in to view your orders.", "error")
            return redirect(url_for("login"))

        user_orders = Order.query.filter_by(user_id=session["user_id"]).order_by(Order.created_at.desc()).all()
        return render_template("orders.html", orders=user_orders)

    @app.route("/admin/seed-menu")
    def seed_menu():
        if session.get("user_role") != "admin":
            return "Forbidden", 403

        add_menu_item("Cheeseburger", 8.99, "main", ["beef", "popular"])
        add_menu_item("Veggie Wrap", 7.49, "main", ["vegetarian"])
        add_menu_item("Fries", 2.99, "side", ["popular"])
        return redirect(url_for("menu"))

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)