"""Menu blueprint — food menu listing and search."""

from flask import Blueprint, render_template, request, jsonify
from app.models import MenuItem, Category

menu_bp = Blueprint('menu', __name__)


@menu_bp.route('/')
def index():
    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order).all()
    selected_cat = request.args.get('category', '')
    food_type    = request.args.get('food_type', '')
    spice_level  = request.args.get('spice_level', '')
    search_q     = request.args.get('q', '').strip()

    query = MenuItem.query.filter_by(is_available=True)

    if selected_cat:
        cat = Category.query.filter_by(name=selected_cat).first()
        if cat:
            query = query.filter_by(category_id=cat.id)

    if food_type in ('vegetarian', 'non_vegetarian'):
        query = query.filter_by(food_type=food_type)

    if spice_level in ('mild', 'medium', 'spicy', 'extra_spicy'):
        query = query.filter_by(spice_level=spice_level)

    if search_q:
        query = query.filter(MenuItem.name.ilike(f'%{search_q}%'))

    items = query.all()

    return render_template('menu.html',
                           items=items,
                           categories=categories,
                           selected_cat=selected_cat,
                           food_type=food_type,
                           spice_level=spice_level,
                           search_q=search_q)


@menu_bp.route('/api/items')
def api_items():
    """JSON API endpoint for dynamic filtering."""
    category_name = request.args.get('category', '')
    food_type     = request.args.get('food_type', '')
    spice_level   = request.args.get('spice_level', '')
    search_q      = request.args.get('q', '').strip()

    query = MenuItem.query.filter_by(is_available=True)

    if category_name:
        cat = Category.query.filter_by(name=category_name).first()
        if cat:
            query = query.filter_by(category_id=cat.id)

    if food_type in ('vegetarian', 'non_vegetarian'):
        query = query.filter_by(food_type=food_type)

    if spice_level in ('mild', 'medium', 'spicy', 'extra_spicy'):
        query = query.filter_by(spice_level=spice_level)

    if search_q:
        query = query.filter(MenuItem.name.ilike(f'%{search_q}%'))

    items = query.all()
    return jsonify([item.to_dict() for item in items])


@menu_bp.route('/item/<int:item_id>')
def item_detail(item_id):
    item = MenuItem.query.get_or_404(item_id)
    related = (MenuItem.query
               .filter_by(category_id=item.category_id, is_available=True)
               .filter(MenuItem.id != item_id)
               .limit(4).all())
    return render_template('item_detail.html', item=item, related=related)
