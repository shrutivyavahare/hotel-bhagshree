"""
Hotel Bhagshree — Database Models
All SQLAlchemy ORM models with relationships, constraints, and validations.
"""

from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager


# ── Login Manager ────────────────────────────────────────────────────────────

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(AdminUser, int(user_id))


# ── Base Model ───────────────────────────────────────────────────────────────

class BaseModel(db.Model):
    """Abstract base model with explicit constructor for IDE static typing."""
    __abstract__ = True

    def __init__(self, **kwargs):
        super().__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)


# ── Admin User ───────────────────────────────────────────────────────────────

class AdminUser(BaseModel, UserMixin):
    __tablename__ = 'admin_users'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name     = db.Column(db.String(120))
    is_super_admin = db.Column(db.Boolean, default=False)
    is_active     = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    last_login    = db.Column(db.DateTime)

    def __repr__(self):
        return f'<AdminUser {self.username}>'


# ── Food Category ────────────────────────────────────────────────────────────

class Category(BaseModel):
    __tablename__ = 'categories'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(80), unique=True, nullable=False)
    icon        = db.Column(db.String(10), default='🍽️')
    description = db.Column(db.Text)
    sort_order  = db.Column(db.Integer, default=0)
    is_active   = db.Column(db.Boolean, default=True)

    items = db.relationship('MenuItem', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'description': self.description,
            'item_count': self.items.filter_by(is_available=True).count()
        }


# ── Menu Item ────────────────────────────────────────────────────────────────

class MenuItem(BaseModel):
    __tablename__ = 'menu_items'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price       = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)

    # Dietary & flavour
    food_type   = db.Column(db.String(20), nullable=False, default='vegetarian')   # 'vegetarian' | 'non_vegetarian'
    spice_level = db.Column(db.String(20), nullable=False, default='mild')          # 'mild' | 'medium' | 'spicy' | 'extra_spicy'
    meal_time   = db.Column(db.String(80), default='lunch,dinner')                 # comma-separated

    # Metadata
    image_file  = db.Column(db.String(200), default='default_dish.jpg')
    is_available = db.Column(db.Boolean, default=True)
    is_featured  = db.Column(db.Boolean, default=False)
    prep_time    = db.Column(db.Integer, default=20)   # minutes
    calories     = db.Column(db.Integer)
    rating       = db.Column(db.Float, default=4.0)
    rating_count = db.Column(db.Integer, default=0)

    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order_items  = db.relationship('OrderItem', backref='menu_item', lazy='dynamic')

    def __repr__(self):
        return f'<MenuItem {self.name} ₹{self.price}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'category': self.category.name if self.category else '',
            'food_type': self.food_type,
            'spice_level': self.spice_level,
            'meal_time': self.meal_time,
            'image_file': self.image_file,
            'is_available': self.is_available,
            'is_featured': self.is_featured,
            'prep_time': self.prep_time,
            'calories': self.calories,
            'rating': self.rating,
        }

    @property
    def meal_times_list(self):
        return [m.strip() for m in self.meal_time.split(',')]


# ── Recommendation Rule ───────────────────────────────────────────────────────

class RecommendationRule(BaseModel):
    __tablename__ = 'recommendation_rules'

    id         = db.Column(db.Integer, primary_key=True)
    rule_id    = db.Column(db.String(10), unique=True, nullable=False)
    rule_name  = db.Column(db.String(200), nullable=False)
    conditions = db.Column(db.Text, nullable=False)   # JSON string of conditions
    action     = db.Column(db.Text, nullable=False)   # Human-readable action description
    priority   = db.Column(db.Integer, default=5)     # Higher = applied first
    is_active  = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Rule {self.rule_id}: {self.rule_name}>'

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'conditions': json.loads(self.conditions),
            'action': self.action,
            'priority': self.priority,
            'is_active': self.is_active,
        }


# ── Order ─────────────────────────────────────────────────────────────────────

class Order(BaseModel):
    __tablename__ = 'orders'

    id              = db.Column(db.Integer, primary_key=True)
    order_id        = db.Column(db.String(20), unique=True, nullable=False)
    customer_name   = db.Column(db.String(120), nullable=False)
    customer_email  = db.Column(db.String(120))
    customer_phone  = db.Column(db.String(15), nullable=False)
    customer_address = db.Column(db.Text)

    order_type      = db.Column(db.String(20), default='dine_in')    # 'dine_in' | 'takeaway'
    payment_method  = db.Column(db.String(30), default='cash')       # 'cash' | 'pay_counter'
    status          = db.Column(db.String(30), default='pending')    # 'pending' | 'confirmed' | 'preparing' | 'ready' | 'delivered' | 'cancelled'

    subtotal        = db.Column(db.Float, default=0.0)
    tax             = db.Column(db.Float, default=0.0)
    total_amount    = db.Column(db.Float, default=0.0)
    notes           = db.Column(db.Text)

    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items           = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f'<Order {self.order_id} — ₹{self.total_amount}>'

    def calculate_totals(self):
        self.subtotal    = sum(i.subtotal for i in self.items)
        self.tax         = round(self.subtotal * 0.05, 2)   # 5% GST
        self.total_amount = round(self.subtotal + self.tax, 2)

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'status': self.status,
            'total_amount': self.total_amount,
            'created_at': self.created_at.strftime('%d %b %Y, %I:%M %p'),
            'items': [i.to_dict() for i in self.items],
        }


class OrderItem(BaseModel):
    __tablename__ = 'order_items'

    id          = db.Column(db.Integer, primary_key=True)
    order_id    = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    quantity    = db.Column(db.Integer, nullable=False, default=1)
    unit_price  = db.Column(db.Float, nullable=False)
    subtotal    = db.Column(db.Float, nullable=False)
    notes       = db.Column(db.String(200))

    def __repr__(self):
        return f'<OrderItem {self.menu_item_id} x{self.quantity}>'

    def to_dict(self):
        return {
            'item_name': self.menu_item.name if self.menu_item else 'Unknown',
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'subtotal': self.subtotal,
        }


# ── Reservation Table ─────────────────────────────────────────────────────────

class ReservationTable(BaseModel):
    __tablename__ = 'reservation_tables'

    id            = db.Column(db.Integer, primary_key=True)
    table_number  = db.Column(db.String(10), unique=True, nullable=False)
    capacity      = db.Column(db.Integer, nullable=False)
    location      = db.Column(db.String(50))   # 'Window' | 'Central' | 'Private' | 'Banquet'
    is_available  = db.Column(db.Boolean, default=True)

    reservations  = db.relationship('Reservation', backref='table', lazy='dynamic')

    def __repr__(self):
        return f'<Table {self.table_number} (cap {self.capacity})>'


# ── Reservation ───────────────────────────────────────────────────────────────

class Reservation(BaseModel):
    __tablename__ = 'reservations'

    id              = db.Column(db.Integer, primary_key=True)
    booking_ref     = db.Column(db.String(20), unique=True, nullable=False)
    customer_name   = db.Column(db.String(120), nullable=False)
    customer_phone  = db.Column(db.String(15), nullable=False)
    customer_email  = db.Column(db.String(120))
    table_id        = db.Column(db.Integer, db.ForeignKey('reservation_tables.id'), nullable=False)

    reservation_date = db.Column(db.Date, nullable=False)
    reservation_time = db.Column(db.String(10), nullable=False)   # 'HH:MM' 24-hr
    guests           = db.Column(db.Integer, nullable=False)
    status           = db.Column(db.String(20), default='confirmed')  # 'confirmed' | 'cancelled' | 'completed'
    special_requests = db.Column(db.Text)

    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Reservation {self.booking_ref} on {self.reservation_date}>'

    def to_dict(self):
        return {
            'id': self.id,
            'booking_ref': self.booking_ref,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'table': self.table.table_number if self.table else '',
            'date': self.reservation_date.strftime('%d %b %Y'),
            'time': self.reservation_time,
            'guests': self.guests,
            'status': self.status,
        }
