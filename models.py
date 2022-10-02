from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class Catalog(db.Model):
    __tablename__ = 'catalog'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    maker = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    prs = db.relationship('PurchaseRequests', secondary='catalog_pr')


class Users(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.Integer, nullable=True)
    role = db.Column(db.String(10), nullable=False)


class Orders(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    created_date = db.Column(db.DateTime, nullable=False)
    required_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Integer, nullable=False)
    # Foreign Key
    procurer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)


class PurchaseRequests(db.Model):
    __tablename__ = 'purchaserequests'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    created_date = db.Column(db.DateTime, nullable=False)
    required_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Integer, nullable=False)
    # Foreign Key
    poc_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    procurer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    # Relationship
    items = db.relationship('Catalog', secondary='catalog_pr', cascade="delete")


#Association tables
class Catalog_Pr(db.Model):
    __tablename__ = 'catalog_pr'
    catalog_id = db.Column(db.Integer, db.ForeignKey('catalog.id'), primary_key=True)
    pr_id = db.Column(db.Integer, db.ForeignKey('purchaserequests.id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    item = db.relationship('Catalog', backref="pr_assoc", cascade="delete")
    pr = db.relationship('PurchaseRequests', backref="item_assoc", cascade="delete")


class Catalog_Order_Vendor(db.Model):
    __tablename__ = 'catalog_order_vendor'
    catalog_id = db.Column(db.Integer, db.ForeignKey('catalog.id'), primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Integer, nullable=False)
    available_date = db.Column(db.Date, nullable=False)
    item = db.relationship('Catalog', backref="item_assoc", cascade="delete")
    order = db.relationship('Orders', backref="order_assoc", cascade="delete")
    vendor = db.relationship('Users', backref="vendor_assoc", cascade="delete")

