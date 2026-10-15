"""
Hotel Bhagshree - Restaurant Management System
Flask Application Factory
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash

db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config=None):
    """Application factory pattern."""
    app = Flask(__name__)

    # ── Configuration ───────────────────────────────────────────────────────────
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'bhagshree-secret-key-2024-very-secure')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bhagshree.db')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

    if config:
        app.config.update(config)

    # ── Extensions ──────────────────────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # ── Blueprints ──────────────────────────────────────────────────────────────
    from app.blueprints.main import main_bp
    from app.blueprints.menu import menu_bp
    from app.blueprints.orders import orders_bp
    from app.blueprints.reservations import reservations_bp
    from app.blueprints.recommendation import recommendation_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.auth import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(menu_bp, url_prefix='/menu')
    app.register_blueprint(orders_bp, url_prefix='/orders')
    app.register_blueprint(reservations_bp, url_prefix='/reservations')
    app.register_blueprint(recommendation_bp, url_prefix='/recommend')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # ── Database Initialization ──────────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        _seed_database()

    return app


def _seed_database():
    """Seed the database with initial data if empty."""
    from app.models import (AdminUser, Category, MenuItem,
                            ReservationTable, RecommendationRule)

    # Admin user initialization
    if not AdminUser.query.first():
        admin = AdminUser(
            username='admin',
            email='admin@hotelbhagshree.com',
            password_hash=generate_password_hash('admin@123', method='pbkdf2:sha256'),
            full_name='Hotel Bhagshree Admin',
            is_super_admin=True
        )
        db.session.add(admin)

    # Categories
    if not Category.query.first():
        categories_data = [
            {'name': 'Maharashtrian', 'icon': '🍛', 'description': 'Authentic flavours from the heart of Maharashtra', 'sort_order': 1},
            {'name': 'Punjabi',       'icon': '🫕', 'description': 'Rich and hearty North Indian classics', 'sort_order': 2},
            {'name': 'South Indian',  'icon': '🥘', 'description': 'Light, nutritious and aromatic southern delights', 'sort_order': 3},
            {'name': 'Chinese',       'icon': '🍜', 'description': 'Indo-Chinese fusion with bold flavours', 'sort_order': 4},
            {'name': 'Snacks',        'icon': '🥙', 'description': 'Quick bites and street food favourites', 'sort_order': 5},
            {'name': 'Desserts',      'icon': '🍮', 'description': 'Indulgent sweets and traditional mithai', 'sort_order': 6},
            {'name': 'Beverages',     'icon': '🥤', 'description': 'Refreshing drinks and signature coolers', 'sort_order': 7},
        ]
        cats = {}
        for c in categories_data:
            cat = Category(**c)
            db.session.add(cat)
            db.session.flush()
            cats[c['name']] = cat.id

        # Menu Items
        menu_items = [
            # ── Maharashtrian ──────────────────────────────────────────────────
            {'name': 'Misal Pav',           'description': 'Legendary Nashik-style spicy sprouted moth bean curry with fiery tarri, crunchy farsan, chopped onions, and soft buttered pav.', 'price': 120, 'category_id': cats['Maharashtrian'], 'food_type': 'vegetarian',     'spice_level': 'spicy',  'is_available': True, 'is_featured': True,  'image_file': 'dish_misal_pav.jpg',     'meal_time': 'breakfast,lunch',   'prep_time': 15, 'calories': 350},
            {'name': 'Varan Bhat',           'description': 'Comforting Maharashtrian dal with steamed rice, a squeeze of lemon and a dollop of homemade ghee. Soul food at its finest.', 'price': 140, 'category_id': cats['Maharashtrian'], 'food_type': 'vegetarian',     'spice_level': 'mild',   'is_available': True, 'is_featured': False, 'image_file': 'dish_varan_bhat.jpg',     'meal_time': 'lunch,dinner',      'prep_time': 20, 'calories': 420},
            {'name': 'Bharli Vangi',         'description': 'Baby brinjals stuffed with a spiced coconut-peanut masala, slow-cooked in a rich gravy. Traditional Maharashtrian comfort food.', 'price': 180, 'category_id': cats['Maharashtrian'], 'food_type': 'vegetarian',     'spice_level': 'medium', 'is_available': True, 'is_featured': True,  'image_file': 'dish_bharli_vangi.jpg',   'meal_time': 'lunch,dinner',      'prep_time': 25, 'calories': 280},
            {'name': 'Chicken Kolhapuri',    'description': 'Fiery chicken curry from the streets of Kolhapur. Cooked in a bold red masala with freshly ground spices. Not for the faint-hearted.', 'price': 280, 'category_id': cats['Maharashtrian'], 'food_type': 'non_vegetarian', 'spice_level': 'extra_spicy', 'is_available': True, 'is_featured': True, 'image_file': 'dish_chicken_kolhapuri.jpg', 'meal_time': 'lunch,dinner', 'prep_time': 35, 'calories': 520},
            {'name': 'Kande Pohe',           'description': 'Light and flavourful flattened rice with mustard seeds, turmeric, green chillies and fresh coconut. The classic Maharashtra morning starter.', 'price': 80,  'category_id': cats['Maharashtrian'], 'food_type': 'vegetarian',     'spice_level': 'mild',   'is_available': True, 'is_featured': False, 'image_file': 'dish_kande_pohe.jpg',     'meal_time': 'breakfast',         'prep_time': 10, 'calories': 220},
            {'name': 'Mutton Sukka',         'description': 'Dry-spiced tender mutton cooked with aromatic Kolhapuri masala, curry leaves and freshly grated coconut. A true weekend special.', 'price': 320, 'category_id': cats['Maharashtrian'], 'food_type': 'non_vegetarian', 'spice_level': 'spicy',  'is_available': True, 'is_featured': False, 'image_file': 'dish_mutton_sukka.jpg',   'meal_time': 'lunch,dinner',      'prep_time': 45, 'calories': 480},
            # ── Punjabi ────────────────────────────────────────────────────────
            {'name': 'Butter Chicken',       'description': 'Succulent chicken in a velvety tomato-cream sauce with aromatic spices. The dish that made Indian cuisine famous across the globe.', 'price': 260, 'category_id': cats['Punjabi'],       'food_type': 'non_vegetarian', 'spice_level': 'mild',   'is_available': True, 'is_featured': True,  'image_file': 'dish_butter_chicken.jpg', 'meal_time': 'lunch,dinner',      'prep_time': 30, 'calories': 480},
            {'name': 'Dal Makhani',          'description': 'Slow-simmered black lentils in a rich butter-cream gravy. Cooked overnight for that distinctive smoky depth of flavour.', 'price': 190, 'category_id': cats['Punjabi'],       'food_type': 'vegetarian',     'spice_level': 'mild',   'is_available': True, 'is_featured': True,  'image_file': 'dish_dal_makhani.jpg',   'meal_time': 'lunch,dinner',      'prep_time': 25, 'calories': 380},
            {'name': 'Paneer Tikka Masala',  'description': 'Tandoor-kissed cottage cheese in a spiced tomato-onion gravy. Perfectly balanced with cream and fresh coriander.', 'price': 220, 'category_id': cats['Punjabi'],       'food_type': 'vegetarian',     'spice_level': 'medium', 'is_available': True, 'is_featured': True,  'image_file': 'dish_paneer_tikka.jpg',   'meal_time': 'lunch,dinner',      'prep_time': 25, 'calories': 420},
            {'name': 'Amritsari Kulcha',     'description': 'Fluffy stuffed kulcha from the holy city of Amritsar, baked in the tandoor and served with chole and pickled onions.', 'price': 160, 'category_id': cats['Punjabi'],       'food_type': 'vegetarian',     'spice_level': 'mild',   'is_available': True, 'is_featured': False, 'image_file': 'dish_amritsari_kulcha.jpg','meal_time': 'breakfast,lunch',   'prep_time': 20, 'calories': 390},
            {'name': 'Tandoori Chicken',     'description': 'Half chicken marinated in yoghurt and spices, charred perfectly in the clay tandoor. Served with mint chutney and laccha onions.', 'price': 300, 'category_id': cats['Punjabi'],       'food_type': 'non_vegetarian', 'spice_level': 'spicy',  'is_available': True, 'is_featured': True,  'image_file': 'dish_tandoori_chicken.jpg','meal_time': 'lunch,dinner',      'prep_time': 35, 'calories': 560},
            {'name': 'Sarson Da Saag',       'description': 'Winter greens slow-cooked and paired with golden makki di roti. Topped with a generous knob of white butter. Pure Punjab.', 'price': 170, 'category_id': cats['Punjabi'],       'food_type': 'vegetarian',     'spice_level': 'mild',   'is_available': True, 'is_featured': False, 'image_file': 'dish_sarson_saag.jpg',   'meal_time': 'lunch,dinner',      'prep_time': 30, 'calories': 310},
            # ── South Indian ───────────────────────────────────────────────────
            {'name': 'Masala Dosa',          'description': 'Crispy fermented rice crepe with spiced potato filling, served with coconut chutney and piping hot sambar. South India on a plate.', 'price': 130, 'category_id': cats['South Indian'],  'food_type': 'vegetarian',     'spice_level': 'mild',   'is_available': True, 'is_featured': True,  'image_file': 'dish_masala_dosa.jpg',   'meal_time': 'breakfast,lunch',   'prep_time': 15, 'calories': 340},
            {'name': 'Idli Sambar',          'description': 'Fluffy steamed rice cakes served with aromatic lentil broth and assorted chutneys. Light, healthy and deeply satisfying.', 'price': 90,  'category_id': cats['South Indian'],  'food_type': 'vegetarian',     'spice_level': 'mild',   'is_available': True, 'is_featured': False, 'image_file': 'dish_idli_sambar.jpg',   'meal_time': 'breakfast',         'prep_time': 10, 'calories': 220},
            {'name': 'Chettinad Chicken',    'description': 'Deeply spiced chicken curry from the Chettinad region of Tamil Nadu, with kalpasi, marathi mokku and freshly ground spices.', 'price': 290, 'category_id': cats['South Indian'],  'food_type': 'non_vegetarian', 'spice_level': 'extra_spicy', 'is_available': True, 'is_featured': True, 'image_file': 'dish_chettinad_chicken.jpg', 'meal_time': 'lunch,dinner', 'prep_time': 40, 'calories': 490},
            {'name': 'Medu Vada',            'description': 'Crispy lentil fritters with a soft centre, served with sambar and fresh coconut chutney. The perfect South Indian snack.', 'price': 100, 'category_id': cats['South Indian'],  'food_type': 'vegetarian',     'spice_level': 'mild',   'is_available': True, 'is_featured': False, 'image_file': 'dish_medu_vada.jpg',     'meal_time': 'breakfast,snacks',  'prep_time': 15, 'calories': 260},
            # ── Chinese ────────────────────────────────────────────────────────
            {'name': 'Veg Manchurian',       'description': 'Crispy vegetable balls tossed in a tangy, spicy Indo-Chinese sauce. The street food favourite that redefined Indian-Chinese.', 'price': 150, 'category_id': cats['Chinese'],       'food_type': 'vegetarian',     'spice_level': 'spicy',  'is_available': True, 'is_featured': False, 'image_file': 'dish_veg_manchurian.jpg','meal_time': 'lunch,dinner,snacks','prep_time': 20, 'calories': 310},
            {'name': 'Chicken Fried Rice',   'description': 'Wok-tossed long-grain rice with shredded chicken, egg, spring onions and soy. Smoky, fragrant and deeply satisfying.', 'price': 200, 'category_id': cats['Chinese'],       'food_type': 'non_vegetarian', 'spice_level': 'medium', 'is_available': True, 'is_featured': False, 'image_file': 'dish_chicken_fried_rice.jpg', 'meal_time': 'lunch,dinner', 'prep_time': 20, 'calories': 450},
            {'name': 'Hakka Noodles',        'description': 'Indo-Chinese style noodles stir-fried with vegetables in a bold soy-chilli sauce. Available vegetarian or with chicken.', 'price': 160, 'category_id': cats['Chinese'],       'food_type': 'vegetarian',     'spice_level': 'medium', 'is_available': True, 'is_featured': False, 'image_file': 'dish_hakka_noodles.jpg', 'meal_time': 'lunch,dinner',      'prep_time': 18, 'calories': 380},
            {'name': 'Chilli Paneer',        'description': 'Golden-fried cottage cheese tossed with green chillies, capsicum and spring onion in a lip-smacking garlic sauce.', 'price': 190, 'category_id': cats['Chinese'],       'food_type': 'vegetarian',     'spice_level': 'spicy',  'is_available': True, 'is_featured': True,  'image_file': 'dish_chilli_paneer.jpg', 'meal_time': 'lunch,dinner',      'prep_time': 22, 'calories': 390},
            # ── Snacks ─────────────────────────────────────────────────────────
            {'name': 'Paneer Tikka',         'description': 'Smoky marinated cottage cheese with peppers on skewers, chargrilled to perfection. Served with tangy green chutney.', 'price': 170, 'category_id': cats['Snacks'],        'food_type': 'vegetarian',     'spice_level': 'medium', 'is_available': True, 'is_featured': True,  'image_file': 'dish_paneer_tikka.jpg',   'meal_time': 'lunch,dinner,snacks','prep_time': 20, 'calories': 290},
            {'name': 'Samosa (2 pcs)',        'description': 'Golden crispy pastry filled with spiced potatoes and peas. The timeless Indian snack, served with three chutneys.', 'price': 60,  'category_id': cats['Snacks'],        'food_type': 'vegetarian',     'spice_level': 'mild',   'is_available': True, 'is_featured': False, 'image_file': 'dish_samosa.jpg',         'meal_time': 'snacks',            'prep_time': 10, 'calories': 240},
            {'name': 'Pav Bhaji',            'description': 'Buttery mashed vegetable medley on a sizzling iron griddle, served with soft toasted pav. Mumbai\'s most-loved street snack.', 'price': 110, 'category_id': cats['Snacks'],        'food_type': 'vegetarian',     'spice_level': 'medium', 'is_available': True, 'is_featured': True,  'image_file': 'dish_pav_bhaji.jpg',     'meal_time': 'lunch,dinner,snacks','prep_time': 15, 'calories': 380},
            # ── Desserts ───────────────────────────────────────────────────────
            {'name': 'Gulab Jamun',          'description': 'Soft khoya dumplings soaked in rose-scented sugar syrup, garnished with crushed pistachios and edible rose petals.', 'price': 90,  'category_id': cats['Desserts'],      'food_type': 'vegetarian',     'spice_level': 'mild',   'is_available': True, 'is_featured': True,  'image_file': 'dish_gulab_jamun.jpg',   'meal_time': 'dessert',           'prep_time': 5,  'calories': 310},
            {'name': 'Ras Malai',            'description': 'Spongy cottage cheese patties in chilled saffron-infused milk, topped with crushed almonds and pistachios. Elegance in a bowl.', 'price': 110, 'category_id': cats['Desserts'],      'food_type': 'vegetarian',     'spice_level': 'mild',   'is_available': True, 'is_featured': True,  'image_file': 'dish_ras_malai.jpg',     'meal_time': 'dessert',           'prep_time': 5,  'calories': 280},
            {'name': 'Kulfi Falooda',        'description': 'Traditional Indian ice cream on a stick with rose syrup, vermicelli and basil seeds. The ultimate Indian summer dessert.', 'price': 100, 'category_id': cats['Desserts'],      'food_type': 'vegetarian',     'spice_level': 'mild',   'is_available': True, 'is_featured': False, 'image_file': 'dish_kulfi_falooda.jpg', 'meal_time': 'dessert',           'prep_time': 5,  'calories': 260},
            # ── Beverages ──────────────────────────────────────────────────────
            {'name': 'Masala Chai',          'description': 'Freshly brewed spiced tea with cardamom, ginger, cinnamon and tulsi. Served in a traditional kullad.', 'price': 40,  'category_id': cats['Beverages'],     'food_type': 'vegetarian',     'spice_level': 'mild',   'is_available': True, 'is_featured': False, 'image_file': 'dish_masala_chai.jpg',   'meal_time': 'breakfast,snacks',  'prep_time': 5,  'calories': 80},
            {'name': 'Fresh Mango Lassi',    'description': 'Thick blended yoghurt with Alphonso mango pulp, a hint of cardamom and crushed ice. Sunshine in a glass.', 'price': 80,  'category_id': cats['Beverages'],     'food_type': 'vegetarian',     'spice_level': 'mild',   'is_available': True, 'is_featured': True,  'image_file': 'dish_mango_lassi.jpg',   'meal_time': 'breakfast,lunch,snacks','prep_time': 5, 'calories': 180},
            {'name': 'Rose Sharbat',         'description': 'Chilled rose petal syrup with basil seeds, fresh lime and a pinch of black salt. A refreshing and aromatic cooler.', 'price': 60,  'category_id': cats['Beverages'],     'food_type': 'vegetarian',     'spice_level': 'mild',   'is_available': True, 'is_featured': False, 'image_file': 'dish_rose_sharbat.jpg',  'meal_time': 'lunch,snacks',      'prep_time': 3,  'calories': 120},
        ]
        for item_data in menu_items:
            item = MenuItem(**item_data)
            db.session.add(item)

    # Restaurant Tables
    if not ReservationTable.query.first():
        tables_data = [
            {'table_number': 'T1', 'capacity': 2,  'location': 'Window',  'is_available': True},
            {'table_number': 'T2', 'capacity': 2,  'location': 'Window',  'is_available': True},
            {'table_number': 'T3', 'capacity': 4,  'location': 'Central', 'is_available': True},
            {'table_number': 'T4', 'capacity': 4,  'location': 'Central', 'is_available': True},
            {'table_number': 'T5', 'capacity': 4,  'location': 'Central', 'is_available': True},
            {'table_number': 'T6', 'capacity': 6,  'location': 'Private', 'is_available': True},
            {'table_number': 'T7', 'capacity': 6,  'location': 'Private', 'is_available': True},
            {'table_number': 'T8', 'capacity': 8,  'location': 'Banquet', 'is_available': True},
            {'table_number': 'T9', 'capacity': 10, 'location': 'Banquet', 'is_available': True},
        ]
        for t in tables_data:
            db.session.add(ReservationTable(**t))

    # Recommendation Rules (25+ meaningful IF-THEN rules)
    if not RecommendationRule.query.first():
        rules = [
            # Vegetarian rules
            {'rule_id': 'R001', 'rule_name': 'Veg Spicy Maharashtrian Lunch',      'conditions': '{"food_type": "vegetarian", "spice_level": "spicy", "cuisine": "Maharashtrian", "meal_time": "lunch"}',                         'action': 'Recommend spicy vegetarian Maharashtrian dishes for lunch', 'priority': 10, 'is_active': True},
            {'rule_id': 'R002', 'rule_name': 'Veg Mild Breakfast',                 'conditions': '{"food_type": "vegetarian", "spice_level": "mild", "meal_time": "breakfast"}',                                                   'action': 'Recommend mild vegetarian breakfast items',              'priority': 9,  'is_active': True},
            {'rule_id': 'R003', 'rule_name': 'Veg Punjabi Dinner High Budget',     'conditions': '{"food_type": "vegetarian", "cuisine": "Punjabi", "meal_time": "dinner", "budget_min": 200}',                                     'action': 'Recommend premium vegetarian Punjabi dinner dishes',      'priority': 9,  'is_active': True},
            {'rule_id': 'R004', 'rule_name': 'Veg South Indian Light',             'conditions': '{"food_type": "vegetarian", "cuisine": "South Indian", "spice_level": "mild"}',                                                   'action': 'Recommend light vegetarian South Indian dishes',          'priority': 8,  'is_active': True},
            {'rule_id': 'R005', 'rule_name': 'Veg Budget Snacks',                  'conditions': '{"food_type": "vegetarian", "budget_max": 120, "category": "Snacks"}',                                                            'action': 'Recommend affordable vegetarian snacks',                 'priority': 7,  'is_active': True},
            {'rule_id': 'R006', 'rule_name': 'Veg Dessert Only',                   'conditions': '{"food_type": "vegetarian", "category": "Desserts"}',                                                                              'action': 'Recommend vegetarian desserts',                          'priority': 8,  'is_active': True},
            {'rule_id': 'R007', 'rule_name': 'Veg Medium Spice Chinese',           'conditions': '{"food_type": "vegetarian", "spice_level": "medium", "cuisine": "Chinese"}',                                                      'action': 'Recommend medium-spiced vegetarian Chinese dishes',       'priority': 7,  'is_active': True},
            {'rule_id': 'R008', 'rule_name': 'Veg Dinner Any Cuisine',             'conditions': '{"food_type": "vegetarian", "meal_time": "dinner"}',                                                                               'action': 'Recommend vegetarian dinner options across all cuisines', 'priority': 5,  'is_active': True},
            # Non-Vegetarian rules
            {'rule_id': 'R009', 'rule_name': 'NonVeg Spicy Maharashtrian',         'conditions': '{"food_type": "non_vegetarian", "cuisine": "Maharashtrian", "spice_level": "spicy"}',                                             'action': 'Recommend spicy non-veg Maharashtrian dishes',           'priority': 10, 'is_active': True},
            {'rule_id': 'R010', 'rule_name': 'NonVeg Punjabi High Budget',         'conditions': '{"food_type": "non_vegetarian", "cuisine": "Punjabi", "budget_min": 250}',                                                         'action': 'Recommend premium Punjabi non-veg dishes',               'priority': 9,  'is_active': True},
            {'rule_id': 'R011', 'rule_name': 'NonVeg Mild Dinner',                 'conditions': '{"food_type": "non_vegetarian", "spice_level": "mild", "meal_time": "dinner"}',                                                   'action': 'Recommend mild non-veg dinner dishes',                   'priority': 8,  'is_active': True},
            {'rule_id': 'R012', 'rule_name': 'NonVeg South Indian Lunch',          'conditions': '{"food_type": "non_vegetarian", "cuisine": "South Indian", "meal_time": "lunch"}',                                                 'action': 'Recommend South Indian non-veg lunch dishes',            'priority': 8,  'is_active': True},
            {'rule_id': 'R013', 'rule_name': 'NonVeg Extra Spicy Any',             'conditions': '{"food_type": "non_vegetarian", "spice_level": "extra_spicy"}',                                                                    'action': 'Recommend extra spicy non-veg dishes for spice lovers',  'priority': 9,  'is_active': True},
            {'rule_id': 'R014', 'rule_name': 'NonVeg Budget Lunch',                'conditions': '{"food_type": "non_vegetarian", "budget_max": 250, "meal_time": "lunch"}',                                                         'action': 'Recommend affordable non-veg lunch options',             'priority': 7,  'is_active': True},
            {'rule_id': 'R015', 'rule_name': 'NonVeg Chinese Medium',              'conditions': '{"food_type": "non_vegetarian", "cuisine": "Chinese", "spice_level": "medium"}',                                                   'action': 'Recommend medium-spiced non-veg Chinese dishes',         'priority': 7,  'is_active': True},
            # Meal time specific
            {'rule_id': 'R016', 'rule_name': 'Breakfast Light',                    'conditions': '{"meal_time": "breakfast", "spice_level": "mild"}',                                                                                'action': 'Recommend mild breakfast items',                          'priority': 8,  'is_active': True},
            {'rule_id': 'R017', 'rule_name': 'Dinner Premium Budget',              'conditions': '{"meal_time": "dinner", "budget_min": 200}',                                                                                       'action': 'Recommend premium dinner dishes',                         'priority': 7,  'is_active': True},
            {'rule_id': 'R018', 'rule_name': 'Snack Time Low Budget',              'conditions': '{"meal_time": "snacks", "budget_max": 150}',                                                                                       'action': 'Recommend affordable snacks',                            'priority': 7,  'is_active': True},
            # Budget-specific rules
            {'rule_id': 'R019', 'rule_name': 'Economy Budget Veg',                 'conditions': '{"food_type": "vegetarian", "budget_max": 100}',                                                                                  'action': 'Recommend budget-friendly vegetarian options under ₹100','priority': 8,  'is_active': True},
            {'rule_id': 'R020', 'rule_name': 'Premium Budget Any',                 'conditions': '{"budget_min": 300}',                                                                                                              'action': 'Recommend premium dishes for generous budgets',          'priority': 6,  'is_active': True},
            # Fallback/broader rules
            {'rule_id': 'R021', 'rule_name': 'Veg Any Medium Budget',              'conditions': '{"food_type": "vegetarian", "budget_min": 100, "budget_max": 250}',                                                               'action': 'Recommend mid-range vegetarian options',                 'priority': 4,  'is_active': True},
            {'rule_id': 'R022', 'rule_name': 'Spicy Lover General',                'conditions': '{"spice_level": "spicy"}',                                                                                                         'action': 'Recommend all spicy dishes across cuisines',             'priority': 3,  'is_active': True},
            {'rule_id': 'R023', 'rule_name': 'Mild Any Cuisine',                   'conditions': '{"spice_level": "mild"}',                                                                                                          'action': 'Recommend mild dishes suitable for all tastes',          'priority': 3,  'is_active': True},
            {'rule_id': 'R024', 'rule_name': 'Beverage Recommendation',            'conditions': '{"category": "Beverages"}',                                                                                                        'action': 'Recommend refreshing beverages',                         'priority': 5,  'is_active': True},
            {'rule_id': 'R025', 'rule_name': 'Dessert After Meal',                 'conditions': '{"meal_time": "dessert"}',                                                                                                         'action': 'Recommend indulgent desserts',                           'priority': 6,  'is_active': True},
            {'rule_id': 'R026', 'rule_name': 'Extra Spicy Veg Option',             'conditions': '{"food_type": "vegetarian", "spice_level": "extra_spicy"}',                                                                       'action': 'Recommend extra spicy vegetarian dishes',                'priority': 8,  'is_active': True},
            {'rule_id': 'R027', 'rule_name': 'Maharashtrian Any Budget',           'conditions': '{"cuisine": "Maharashtrian"}',                                                                                                     'action': 'Recommend authentic Maharashtrian specialties',          'priority': 4,  'is_active': True},
            {'rule_id': 'R028', 'rule_name': 'South Indian Breakfast Special',     'conditions': '{"cuisine": "South Indian", "meal_time": "breakfast"}',                                                                            'action': 'Recommend South Indian breakfast items',                 'priority': 9,  'is_active': True},
        ]
        for r in rules:
            db.session.add(RecommendationRule(**r))

    db.session.commit()
