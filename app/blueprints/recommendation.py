"""Recommendation blueprint — AI-like rule-based food recommendation."""

from flask import Blueprint, render_template, request, jsonify
from app.models import MenuItem, RecommendationRule
from recommendation_engine import get_recommendations, UserPreferences

recommendation_bp = Blueprint('recommendation', __name__)

CUISINES    = ['Any', 'Maharashtrian', 'Punjabi', 'South Indian', 'Chinese', 'Snacks', 'Desserts', 'Beverages']
CATEGORIES  = ['Any', 'Maharashtrian', 'Punjabi', 'South Indian', 'Chinese', 'Snacks', 'Desserts', 'Beverages']
SPICE_LEVELS = ['mild', 'medium', 'spicy', 'extra_spicy']
MEAL_TIMES  = ['breakfast', 'lunch', 'dinner', 'snacks', 'dessert']


@recommendation_bp.route('/', methods=['GET', 'POST'])
def index():
    result = None
    form_data = {}

    if request.method == 'POST':
        food_type   = request.form.get('food_type', 'vegetarian')
        spice_level = request.form.get('spice_level', 'mild')
        cuisine     = request.form.get('cuisine', 'Any')
        budget      = request.form.get('budget', '500')
        meal_time   = request.form.get('meal_time', 'dinner')
        category    = request.form.get('category', 'Any')

        form_data = {
            'food_type': food_type, 'spice_level': spice_level,
            'cuisine': cuisine, 'budget': budget,
            'meal_time': meal_time, 'category': category,
        }

        try:
            budget_float = float(budget)
            if budget_float <= 0:
                raise ValueError('Budget must be positive')
        except (ValueError, TypeError):
            budget_float = 500.0

        prefs = UserPreferences(
            food_type=food_type,
            spice_level=spice_level,
            cuisine=cuisine if cuisine != 'Any' else None,
            budget=budget_float,
            meal_time=meal_time,
            category=category if category != 'Any' else None,
        )

        menu_items  = MenuItem.query.filter_by(is_available=True).all()
        rules_from_db = RecommendationRule.query.filter_by(is_active=True).order_by(
            RecommendationRule.priority.desc()).all()

        result = get_recommendations(prefs, menu_items, rules_from_db)

    return render_template(
        'recommendation.html',
        result=result,
        form_data=form_data,
        cuisines=CUISINES,
        spice_levels=SPICE_LEVELS,
        meal_times=MEAL_TIMES,
        categories=CATEGORIES,
    )


@recommendation_bp.route('/api', methods=['POST'])
def api():
    """JSON API for recommendation (AJAX)."""
    data = request.get_json(silent=True) or {}

    food_type   = data.get('food_type', 'vegetarian')
    spice_level = data.get('spice_level', 'mild')
    cuisine     = data.get('cuisine', None)
    budget      = float(data.get('budget', 500))
    meal_time   = data.get('meal_time', 'dinner')
    category    = data.get('category', None)

    prefs = UserPreferences(
        food_type=food_type, spice_level=spice_level,
        cuisine=cuisine, budget=budget,
        meal_time=meal_time, category=category,
    )

    menu_items    = MenuItem.query.filter_by(is_available=True).all()
    rules_from_db = RecommendationRule.query.filter_by(is_active=True).all()
    result        = get_recommendations(prefs, menu_items, rules_from_db)

    return jsonify({
        'recommendations': [
            {
                'id': d.dish_id, 'name': d.name, 'description': d.description,
                'price': d.price, 'food_type': d.food_type, 'spice_level': d.spice_level,
                'category': d.category, 'image_file': d.image_file,
                'prep_time': d.prep_time, 'calories': d.calories, 'rating': d.rating,
                'explanation': d.explanation, 'confidence_score': d.confidence_score,
                'matched_rules': [{'rule_id': r.rule_id, 'rule_name': r.rule_name, 'action': r.action} for r in d.matched_rules],
            }
            for d in result.recommendations
        ],
        'fired_rules': [
            {'rule_id': r.rule_id, 'rule_name': r.rule_name, 'action': r.action,
             'priority': r.priority, 'matched_conditions': r.matched_conditions}
            for r in result.fired_rules
        ],
        'total_rules_checked': result.total_rules_checked,
        'total_rules_fired':   result.total_rules_fired,
        'session_notes':       result.session_notes,
    })
