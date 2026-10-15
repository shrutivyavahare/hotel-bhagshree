"""Admin blueprint — dashboard and management."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta
from sqlalchemy import func

from app.models import (AdminUser, Category, MenuItem, Order, OrderItem,
                         Reservation, ReservationTable, RecommendationRule)
from app import db

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator for admin-only routes."""
    from functools import wraps
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated


# ── Dashboard ─────────────────────────────────────────────────────────────────

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    today = date.today()
    week_ago = today - timedelta(days=7)

    total_orders     = Order.query.count()
    total_revenue    = db.session.query(func.sum(Order.total_amount)).scalar() or 0
    total_reservations = Reservation.query.count()
    total_menu_items = MenuItem.query.count()

    today_orders     = Order.query.filter(func.date(Order.created_at) == today).count()
    today_revenue    = db.session.query(func.sum(Order.total_amount)).filter(
                        func.date(Order.created_at) == today).scalar() or 0
    today_reservations = Reservation.query.filter_by(reservation_date=today).count()

    recent_orders    = Order.query.order_by(Order.created_at.desc()).limit(8).all()
    recent_reservations = Reservation.query.order_by(Reservation.created_at.desc()).limit(8).all()

    pending_orders   = Order.query.filter_by(status='pending').count()
    confirmed_orders = Order.query.filter_by(status='confirmed').count()
    preparing_orders = Order.query.filter_by(status='preparing').count()

    return render_template('admin/dashboard.html',
                           total_orders=total_orders,
                           total_revenue=total_revenue,
                           total_reservations=total_reservations,
                           total_menu_items=total_menu_items,
                           today_orders=today_orders,
                           today_revenue=today_revenue,
                           today_reservations=today_reservations,
                           recent_orders=recent_orders,
                           recent_reservations=recent_reservations,
                           pending_orders=pending_orders,
                           confirmed_orders=confirmed_orders,
                           preparing_orders=preparing_orders)


# ── Menu Management ───────────────────────────────────────────────────────────

@admin_bp.route('/menu')
@admin_required
def menu_list():
    items = MenuItem.query.order_by(MenuItem.category_id, MenuItem.name).all()
    return render_template('admin/menu_list.html', items=items)


@admin_bp.route('/menu/add', methods=['GET', 'POST'])
@admin_required
def menu_add():
    categories = Category.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        try:
            item = MenuItem(
                name        = request.form['name'].strip(),
                description = request.form['description'].strip(),
                price       = float(request.form['price']),
                category_id = int(request.form['category_id']),
                food_type   = request.form.get('food_type', 'vegetarian'),
                spice_level = request.form.get('spice_level', 'mild'),
                meal_time   = request.form.get('meal_time', 'lunch,dinner'),
                is_available = request.form.get('is_available') == 'on',
                is_featured  = request.form.get('is_featured') == 'on',
                prep_time    = int(request.form.get('prep_time', 20)),
                calories     = request.form.get('calories') or None,
            )
            if item.calories:
                item.calories = int(item.calories)
            db.session.add(item)
            db.session.commit()
            flash(f'"{item.name}" added successfully!', 'success')
            return redirect(url_for('admin.menu_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'error')

    return render_template('admin/menu_form.html', item=None, categories=categories, action='Add')


@admin_bp.route('/menu/<int:item_id>/edit', methods=['GET', 'POST'])
@admin_required
def menu_edit(item_id):
    item = MenuItem.query.get_or_404(item_id)
    categories = Category.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        try:
            item.name        = request.form['name'].strip()
            item.description = request.form['description'].strip()
            item.price       = float(request.form['price'])
            item.category_id = int(request.form['category_id'])
            item.food_type   = request.form.get('food_type', 'vegetarian')
            item.spice_level = request.form.get('spice_level', 'mild')
            item.meal_time   = request.form.get('meal_time', 'lunch,dinner')
            item.is_available = request.form.get('is_available') == 'on'
            item.is_featured  = request.form.get('is_featured') == 'on'
            item.prep_time    = int(request.form.get('prep_time', 20))
            cal = request.form.get('calories')
            item.calories = int(cal) if cal else None
            db.session.commit()
            flash(f'"{item.name}" updated successfully!', 'success')
            return redirect(url_for('admin.menu_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'error')

    return render_template('admin/menu_form.html', item=item, categories=categories, action='Edit')


@admin_bp.route('/menu/<int:item_id>/delete', methods=['POST'])
@admin_required
def menu_delete(item_id):
    item = MenuItem.query.get_or_404(item_id)
    name = item.name
    try:
        db.session.delete(item)
        db.session.commit()
        flash(f'"{name}" deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {e}', 'error')
    return redirect(url_for('admin.menu_list'))


@admin_bp.route('/menu/<int:item_id>/toggle-availability', methods=['POST'])
@admin_required
def toggle_availability(item_id):
    item = MenuItem.query.get_or_404(item_id)
    item.is_available = not item.is_available
    db.session.commit()
    status = 'available' if item.is_available else 'unavailable'
    return jsonify({'success': True, 'is_available': item.is_available,
                    'message': f'{item.name} is now {status}.'})


# ── Order Management ──────────────────────────────────────────────────────────

@admin_bp.route('/orders')
@admin_required
def orders():
    status_filter = request.args.get('status', '')
    query = Order.query.order_by(Order.created_at.desc())
    if status_filter:
        query = query.filter_by(status=status_filter)
    orders = query.limit(100).all()
    return render_template('admin/orders.html', orders=orders, status_filter=status_filter)


@admin_bp.route('/orders/<int:order_id>/update-status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status') or (request.get_json(silent=True) or {}).get('status')
    valid_statuses = ['pending', 'confirmed', 'preparing', 'ready', 'delivered', 'cancelled']
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400
    order.status = new_status
    db.session.commit()
    return jsonify({'success': True, 'new_status': new_status})


# ── Reservation Management ────────────────────────────────────────────────────

@admin_bp.route('/reservations')
@admin_required
def reservations():
    date_filter = request.args.get('date', '')
    query = Reservation.query.order_by(Reservation.reservation_date.desc(),
                                        Reservation.reservation_time)
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter_by(reservation_date=filter_date)
        except ValueError:
            pass
    reservations = query.limit(100).all()
    return render_template('admin/reservations.html',
                           reservations=reservations, date_filter=date_filter)


@admin_bp.route('/reservations/<int:res_id>/cancel', methods=['POST'])
@admin_required
def cancel_reservation(res_id):
    res = Reservation.query.get_or_404(res_id)
    res.status = 'cancelled'
    db.session.commit()
    flash(f'Reservation {res.booking_ref} cancelled.', 'success')
    return redirect(url_for('admin.reservations'))


# ── Rules Management ──────────────────────────────────────────────────────────

@admin_bp.route('/rules')
@admin_required
def rules_list():
    rules = RecommendationRule.query.order_by(RecommendationRule.priority.desc()).all()
    return render_template('admin/rules_list.html', rules=rules)


@admin_bp.route('/rules/<int:rule_id>/toggle', methods=['POST'])
@admin_required
def toggle_rule(rule_id):
    rule = RecommendationRule.query.get_or_404(rule_id)
    rule.is_active = not rule.is_active
    db.session.commit()
    status = 'enabled' if rule.is_active else 'disabled'
    return jsonify({'success': True, 'is_active': rule.is_active,
                    'message': f'Rule {rule.rule_id} {status}.'})


# ── Categories Management ─────────────────────────────────────────────────────

@admin_bp.route('/categories')
@admin_required
def categories():
    cats = Category.query.order_by(Category.sort_order).all()
    return render_template('admin/categories.html', categories=cats)
