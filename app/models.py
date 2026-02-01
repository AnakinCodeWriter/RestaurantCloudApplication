from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="customer", nullable=False)

    def __repr__(self):
        return f"<User {self.email}>"
    
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), default="created", nullable=False)
    total = db.Column(db.Float, default=0.0, nullable=False)

    user = db.relationship("User", backref="orders")


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)

    #reference the firestore document id
    menu_item_id = db.Column(db.String(100), nullable=False)

    #if menu changes later this keeps snapshots so the order stays accurate
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)

    quantity = db.Column(db.Integer, default=1, nullable=False)

    order = db.relationship("Order", backref="items")