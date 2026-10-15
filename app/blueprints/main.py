"""Main blueprint — homepage and static pages."""

from flask import Blueprint, render_template
from app.models import MenuItem, Category

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    featured_items = MenuItem.query.filter_by(is_featured=True, is_available=True).limit(6).all()
    categories     = Category.query.filter_by(is_active=True).order_by(Category.sort_order).all()
    return render_template('index.html', featured_items=featured_items, categories=categories)


@main_bp.route('/about')
def about():
    return render_template('about.html')


@main_bp.route('/contact')
def contact():
    return render_template('contact.html')
