"""Orders blueprint — cart, checkout, order management."""

import uuid
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from app.models import MenuItem, Order, OrderItem
from app import db

orders_bp = Blueprint('orders', __name__)


def _get_cart() -> dict:
    return session.get('cart', {})


def _save_cart(cart: dict):
    session['cart'] = cart
    session.modified = True


def _generate_order_id() -> str:
    return 'BHG' + uuid.uuid4().hex[:8].upper()


# ── Cart API ──────────────────────────────────────────────────────────────────

@orders_bp.route('/cart')
def cart():
    cart = _get_cart()
    items = []
    subtotal = 0.0
    for item_id, qty in cart.items():
        menu_item = db.session.get(MenuItem, int(item_id))
        if menu_item and menu_item.is_available:
            line_total = menu_item.price * qty
            subtotal  += line_total
            items.append({'item': menu_item, 'qty': qty, 'line_total': line_total})
    tax   = round(subtotal * 0.05, 2)
    total = round(subtotal + tax, 2)
    return render_template('cart.html', cart_items=items, subtotal=subtotal, tax=tax, total=total)


@orders_bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    data    = request.get_json(silent=True) or {}
    item_id = str(data.get('item_id', ''))
    qty     = int(data.get('qty', 1))

    if not item_id:
        return jsonify({'success': False, 'message': 'Invalid item'}), 400

    item = db.session.get(MenuItem, int(item_id))
    if not item or not item.is_available:
        return jsonify({'success': False, 'message': 'Item unavailable'}), 400

    cart = _get_cart()
    cart[item_id] = cart.get(item_id, 0) + qty
    _save_cart(cart)

    cart_count = sum(cart.values())
    return jsonify({'success': True, 'message': f'{item.name} added to cart', 'cart_count': cart_count})


@orders_bp.route('/cart/update', methods=['POST'])
def update_cart():
    data    = request.get_json(silent=True) or {}
    item_id = str(data.get('item_id', ''))
    qty     = int(data.get('qty', 1))
    cart    = _get_cart()

    if item_id in cart:
        if qty <= 0:
            del cart[item_id]
        else:
            cart[item_id] = qty
        _save_cart(cart)

    cart_count = sum(cart.values())
    return jsonify({'success': True, 'cart_count': cart_count})


@orders_bp.route('/cart/remove', methods=['POST'])
def remove_from_cart():
    data    = request.get_json(silent=True) or {}
    item_id = str(data.get('item_id', ''))
    cart    = _get_cart()

    if item_id in cart:
        del cart[item_id]
        _save_cart(cart)

    cart_count = sum(cart.values())
    return jsonify({'success': True, 'cart_count': cart_count})


@orders_bp.route('/cart/count')
def cart_count():
    cart = _get_cart()
    return jsonify({'count': sum(cart.values())})


# ── Checkout ──────────────────────────────────────────────────────────────────

@orders_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = _get_cart()
    if not cart:
        flash('Your cart is empty.', 'info')
        return redirect(url_for('menu.index'))

    # Build cart items for display
    items      = []
    subtotal   = 0.0
    for item_id, qty in cart.items():
        menu_item = db.session.get(MenuItem, int(item_id))
        if menu_item and menu_item.is_available:
            line_total = menu_item.price * qty
            subtotal  += line_total
            items.append({'item': menu_item, 'qty': qty, 'line_total': line_total})

    tax   = round(subtotal * 0.05, 2)
    total = round(subtotal + tax, 2)

    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        phone   = request.form.get('phone', '').strip()
        email   = request.form.get('email', '').strip()
        payment = request.form.get('payment', 'cash')
        notes   = request.form.get('notes', '').strip()

        # Input validation
        errors = []
        if not name:
            errors.append('Name is required.')
        if not phone or len(phone) < 10:
            errors.append('Valid 10-digit phone number required.')
        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('checkout.html', cart_items=items,
                                   subtotal=subtotal, tax=tax, total=total)

        # Create order
        order = Order(
            order_id       = _generate_order_id(),
            customer_name  = name,
            customer_email = email,
            customer_phone = phone,
            payment_method = payment,
            notes          = notes,
            status         = 'confirmed',
            subtotal       = subtotal,
            tax            = tax,
            total_amount   = total,
        )
        db.session.add(order)
        db.session.flush()

        for item_id, qty in cart.items():
            menu_item = db.session.get(MenuItem, int(item_id))
            if menu_item:
                oi = OrderItem(
                    order_id     = order.id,
                    menu_item_id = menu_item.id,
                    quantity     = qty,
                    unit_price   = menu_item.price,
                    subtotal     = menu_item.price * qty,
                )
                db.session.add(oi)

        db.session.commit()
        _save_cart({})   # Clear cart

        return redirect(url_for('orders.confirmation', order_id=order.order_id))

    return render_template('checkout.html', cart_items=items,
                           subtotal=subtotal, tax=tax, total=total)


@orders_bp.route('/confirmation/<order_id>')
def confirmation(order_id):
    order = Order.query.filter_by(order_id=order_id).first_or_404()
    return render_template('order_confirmation.html', order=order)


@orders_bp.route('/history')
def history():
    phone = request.args.get('phone', '').strip()
    orders = []
    if phone:
        orders = Order.query.filter_by(customer_phone=phone).order_by(Order.created_at.desc()).all()
    return render_template('order_history.html', orders=orders, phone=phone)


@orders_bp.route('/status/<order_id>')
def status(order_id):
    order = Order.query.filter_by(order_id=order_id).first_or_404()
    return render_template('order_status.html', order=order)
