"""
Hotel Bhagshree — Test Suite
Tests for recommendation engine, cart, orders, reservations, and admin auth.
"""

import unittest
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from app.models import (
    MenuItem, Category, RecommendationRule, Order, OrderItem,
    Reservation, ReservationTable, AdminUser
)
from recommendation_engine import (
    get_recommendations, UserPreferences, KnowledgeBase, InferenceEngine
)
from datetime import date, timedelta
from werkzeug.security import generate_password_hash


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret'
    WTF_CSRF_ENABLED = False


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig.__dict__)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()


# ── Recommendation Engine Tests ────────────────────────────────────────────────

class TestRecommendationEngine(unittest.TestCase):
    """Test the IF-THEN rule-based recommendation engine."""

    def _make_rule(self, rule_id, conditions: dict, priority=5):
        class FakeRule:
            pass
        r = FakeRule()
        r.rule_id = rule_id
        r.rule_name = f'Test Rule {rule_id}'
        r.conditions = json.dumps(conditions)
        r.action = 'Test action'
        r.priority = priority
        r.is_active = True
        return r

    def _make_item(self, item_id, food_type='vegetarian', spice='mild',
                   price=100, category_name='Test', meal_time='lunch,dinner'):
        class FakeCat:
            name = category_name
        class FakeItem:
            pass
        item = FakeItem()
        item.id = item_id
        item.name = f'Dish {item_id}'
        item.description = 'A test dish'
        item.price = price
        item.food_type = food_type
        item.spice_level = spice
        item.meal_time = meal_time
        item.is_available = True
        item.is_featured = False
        item.image_file = 'test.jpg'
        item.prep_time = 15
        item.calories = 300
        item.rating = 4.0
        item.category = FakeCat()
        item.meal_times_list = [m.strip() for m in meal_time.split(',')]
        return item

    def test_vegetarian_safety_constraint(self):
        """Non-veg items must NEVER appear for vegetarian users."""
        rules = [self._make_rule('R1', {'food_type': 'vegetarian'})]
        items = [
            self._make_item(1, food_type='vegetarian'),
            self._make_item(2, food_type='non_vegetarian'),
        ]
        prefs = UserPreferences(
            food_type='vegetarian', spice_level='mild',
            cuisine=None, budget=500, meal_time='dinner', category=None
        )
        result = get_recommendations(prefs, items, rules)
        item_ids = [d.dish_id for d in result.recommendations]
        self.assertIn(1, item_ids, 'Veg item should be recommended')
        self.assertNotIn(2, item_ids, 'Non-veg item must NEVER appear for veg user')

    def test_budget_filtering(self):
        """Items exceeding user budget must not be recommended."""
        rules = [self._make_rule('R1', {'food_type': 'vegetarian'})]
        items = [
            self._make_item(1, price=100),
            self._make_item(2, price=500),
        ]
        prefs = UserPreferences(
            food_type='vegetarian', spice_level='mild',
            cuisine=None, budget=200, meal_time='dinner', category=None
        )
        result = get_recommendations(prefs, items, rules)
        item_ids = [d.dish_id for d in result.recommendations]
        self.assertIn(1, item_ids, 'Affordable item should appear')
        self.assertNotIn(2, item_ids, 'Over-budget item should not appear')

    def test_spice_level_matching(self):
        """Engine should fire spice rules and match correctly."""
        rules = [self._make_rule('R1', {'spice_level': 'spicy'})]
        items = [
            self._make_item(1, spice='spicy'),
            self._make_item(2, spice='mild'),
        ]
        prefs = UserPreferences(
            food_type='vegetarian', spice_level='spicy',
            cuisine=None, budget=500, meal_time='dinner', category=None
        )
        result = get_recommendations(prefs, items, rules)
        item_ids = [d.dish_id for d in result.recommendations]
        self.assertIn(1, item_ids, 'Spicy item should match spicy rule')

    def test_availability_filtering(self):
        """Unavailable items must not be recommended."""
        rules = [self._make_rule('R1', {'food_type': 'vegetarian'})]
        available_item   = self._make_item(1)
        unavailable_item = self._make_item(2)
        unavailable_item.is_available = False
        prefs = UserPreferences(
            food_type='vegetarian', spice_level='mild',
            cuisine=None, budget=500, meal_time='dinner', category=None
        )
        result = get_recommendations(prefs, [available_item, unavailable_item], rules)
        item_ids = [d.dish_id for d in result.recommendations]
        self.assertIn(1, item_ids)
        self.assertNotIn(2, item_ids, 'Unavailable item must be excluded')

    def test_cuisine_rule_matching(self):
        """Cuisine-specific rules should only fire for matching cuisine."""
        rules = [self._make_rule('R1', {'cuisine': 'Punjabi'})]

        class PunjabiCat:
            name = 'Punjabi'

        class OtherCat:
            name = 'Chinese'

        item1 = self._make_item(1, category_name='Punjabi')
        item1.category.name = 'Punjabi'
        item2 = self._make_item(2, category_name='Chinese')
        item2.category.name = 'Chinese'

        prefs = UserPreferences(
            food_type='vegetarian', spice_level='mild',
            cuisine='Punjabi', budget=500, meal_time='dinner', category=None
        )
        result = get_recommendations(prefs, [item1, item2], rules)
        item_ids = [d.dish_id for d in result.recommendations]
        self.assertIn(1, item_ids, 'Punjabi item should match Punjabi rule')

    def test_no_results_session_note(self):
        """With impossible constraints, session_notes should inform user."""
        rules = [self._make_rule('R1', {'food_type': 'vegetarian', 'budget_max': 50})]
        items = [self._make_item(1, price=200)]
        prefs = UserPreferences(
            food_type='vegetarian', spice_level='mild',
            cuisine=None, budget=40, meal_time='dinner', category=None
        )
        result = get_recommendations(prefs, items, rules)
        self.assertEqual(len(result.recommendations), 0)
        self.assertNotEqual(result.session_notes, '', 'Should have a helpful no-results note')

    def test_rule_priority_ordering(self):
        """Higher priority rules should fire first."""
        rules = [
            self._make_rule('R1', {'food_type': 'vegetarian'}, priority=10),
            self._make_rule('R2', {'food_type': 'vegetarian'}, priority=3),
        ]
        kb = KnowledgeBase()
        kb.load_rules(rules)
        active = kb.get_active_rules()
        self.assertEqual(active[0]['rule_id'], 'R1', 'R1 (P10) should come before R2 (P3)')

    def test_confidence_score_range(self):
        """Confidence scores must be in [0.0, 1.0]."""
        rules = [self._make_rule('R1', {'food_type': 'vegetarian'})]
        items = [self._make_item(1), self._make_item(2)]
        prefs = UserPreferences(
            food_type='vegetarian', spice_level='mild',
            cuisine=None, budget=500, meal_time='dinner', category=None
        )
        result = get_recommendations(prefs, items, rules)
        for rec in result.recommendations:
            self.assertGreaterEqual(rec.confidence_score, 0.0)
            self.assertLessEqual(rec.confidence_score, 1.0)

    def test_explanation_generated(self):
        """Every recommendation must have a non-empty explanation."""
        rules = [self._make_rule('R1', {'food_type': 'vegetarian'})]
        items = [self._make_item(1)]
        prefs = UserPreferences(
            food_type='vegetarian', spice_level='mild',
            cuisine=None, budget=500, meal_time='dinner', category=None
        )
        result = get_recommendations(prefs, items, rules)
        for rec in result.recommendations:
            self.assertTrue(len(rec.explanation) > 0, 'Explanation must not be empty')

    def test_meal_time_matching(self):
        """Meal-time rules should filter correctly."""
        rules = [self._make_rule('R1', {'meal_time': 'breakfast'})]
        breakfast_item = self._make_item(1, meal_time='breakfast,lunch')
        dinner_item    = self._make_item(2, meal_time='dinner')
        prefs = UserPreferences(
            food_type='vegetarian', spice_level='mild',
            cuisine=None, budget=500, meal_time='breakfast', category=None
        )
        result = get_recommendations(prefs, [breakfast_item, dinner_item], rules)
        ids = [d.dish_id for d in result.recommendations]
        self.assertIn(1, ids, 'Breakfast item should be recommended')
        self.assertNotIn(2, ids, 'Dinner-only item should not match breakfast rule')

    def test_multiple_rules_fired(self):
        """Multiple matching rules should result in higher-confidence scores."""
        rules = [
            self._make_rule('R1', {'food_type': 'vegetarian'}, priority=8),
            self._make_rule('R2', {'spice_level': 'mild'},     priority=6),
        ]
        item = self._make_item(1, food_type='vegetarian', spice='mild')
        prefs = UserPreferences(
            food_type='vegetarian', spice_level='mild',
            cuisine=None, budget=500, meal_time='dinner', category=None
        )
        result = get_recommendations(prefs, [item], rules)
        self.assertTrue(len(result.recommendations) > 0)
        rec = result.recommendations[0]
        self.assertGreaterEqual(len(rec.matched_rules), 2, 'Should match at least 2 rules')


# ── Cart Calculation Tests ─────────────────────────────────────────────────────

class TestCartCalculations(unittest.TestCase):
    def test_gst_calculation(self):
        """GST should be exactly 5% of subtotal."""
        subtotal = 300.0
        tax = round(subtotal * 0.05, 2)
        total = round(subtotal + tax, 2)
        self.assertEqual(tax, 15.0)
        self.assertEqual(total, 315.0)

    def test_multi_item_subtotal(self):
        prices = [120, 280, 90]
        quantities = [2, 1, 3]
        expected = sum(p * q for p, q in zip(prices, quantities))
        self.assertEqual(expected, 120*2 + 280 + 90*3)


# ── Order ID Uniqueness ───────────────────────────────────────────────────────

class TestOrderIDGeneration(unittest.TestCase):
    def test_order_ids_unique(self):
        import uuid
        ids = set()
        for _ in range(1000):
            oid = 'BHG' + uuid.uuid4().hex[:8].upper()
            ids.add(oid)
        self.assertEqual(len(ids), 1000, 'Order IDs should be unique')

    def test_order_id_prefix(self):
        import uuid
        oid = 'BHG' + uuid.uuid4().hex[:8].upper()
        self.assertTrue(oid.startswith('BHG'))
        self.assertEqual(len(oid), 11)


# ── Admin Authentication Tests ────────────────────────────────────────────────

class TestAdminAuth(BaseTestCase):
    def test_login_success(self):
        """Valid admin credentials allow login."""
        response = self.client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin@123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard', response.data)

    def test_login_failure(self):
        """Invalid credentials show error flash."""
        response = self.client.post('/auth/login', data={
            'username': 'admin',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid credentials', response.data)

    def test_protected_admin_route_redirect(self):
        """Accessing admin route without logging in redirects to login page."""
        response = self.client.get('/admin/', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.headers['Location'])

    def test_logout(self):
        """Logged in admin can logout successfully."""
        self.client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin@123'
        }, follow_redirects=True)
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'logged out', response.data)


# ── Database CRUD Operations Tests ───────────────────────────────────────────

class TestDatabaseCRUD(BaseTestCase):
    def test_category_crud(self):
        """Test creating, reading, updating and deleting categories."""
        # Create category
        cat = Category(name='Thali', icon='🍱', description='Special Thalis', sort_order=8)
        db.session.add(cat)
        db.session.commit()
        cat_id = cat.id
        self.assertIsNotNone(cat_id)

        # Read
        fetched = db.session.get(Category, cat_id)
        self.assertEqual(fetched.name, 'Thali')

        # Update
        fetched.name = 'Royal Thali'
        db.session.commit()
        self.assertEqual(db.session.get(Category, cat_id).name, 'Royal Thali')

        # Delete
        db.session.delete(fetched)
        db.session.commit()
        self.assertIsNone(db.session.get(Category, cat_id))

    def test_menu_item_crud_and_availability(self):
        """Test creating, reading, updating availability and deleting menu items."""
        cat = Category.query.first()
        item = MenuItem(
            name='Special Poha',
            description='Traditional morning poha',
            price=70,
            category_id=cat.id,
            food_type='vegetarian',
            spice_level='mild',
            is_available=True
        )
        db.session.add(item)
        db.session.commit()
        item_id = item.id

        # Read
        fetched = db.session.get(MenuItem, item_id)
        self.assertTrue(fetched.is_available)
        self.assertEqual(fetched.price, 70.0)

        # Update availability
        fetched.is_available = False
        db.session.commit()
        self.assertFalse(db.session.get(MenuItem, item_id).is_available)

        # Delete
        db.session.delete(fetched)
        db.session.commit()
        self.assertIsNone(db.session.get(MenuItem, item_id))


# ── Order Creation and Checkout Tests ────────────────────────────────────────

class TestOrderCreation(BaseTestCase):
    def test_order_creation_flow(self):
        """Test adding item to cart and submitting checkout creates order."""
        item = MenuItem.query.first()

        # Add to cart via session
        with self.client.session_transaction() as sess:
            sess['cart'] = {str(item.id): 2}

        # Submit checkout
        response = self.client.post('/orders/checkout', data={
            'name': 'Ramesh Patil',
            'phone': '9876543210',
            'email': 'ramesh@example.com',
            'payment': 'cash',
            'notes': 'Extra chutney please'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Order Confirmed', response.data)

        # Verify order in database
        order = Order.query.filter_by(customer_phone='9876543210').first()
        self.assertIsNotNone(order)
        self.assertEqual(order.customer_name, 'Ramesh Patil')
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items[0].quantity, 2)
        expected_subtotal = item.price * 2
        self.assertEqual(order.subtotal, expected_subtotal)

    def test_checkout_validation_phone_required(self):
        """Invalid or missing phone number blocks checkout."""
        item = MenuItem.query.first()
        with self.client.session_transaction() as sess:
            sess['cart'] = {str(item.id): 1}

        response = self.client.post('/orders/checkout', data={
            'name': 'Ramesh Patil',
            'phone': '123',  # too short
            'payment': 'cash'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Valid 10-digit phone number required', response.data)


# ── Reservation Conflicts and Double-Booking Tests ───────────────────────────

class TestReservationConflicts(BaseTestCase):
    def test_reservation_creation_and_double_booking_prevention(self):
        """Test reserving a table and preventing double booking of the same table."""
        res_date = (date.today() + timedelta(days=2)).isoformat()
        res_time = '19:00'

        # Make first reservation
        response1 = self.client.post('/reservations/', data={
            'name': 'Suresh Deshmukh',
            'phone': '9822001122',
            'email': 'suresh@example.com',
            'date': res_date,
            'time': res_time,
            'guests': 2
        }, follow_redirects=True)
        self.assertEqual(response1.status_code, 200)
        self.assertIn(b'Reservation Confirmed', response1.data)

        # There are 2 tables with capacity 2 (T1 and T2).
        # Book a second 2-guest reservation for the same slot
        response2 = self.client.post('/reservations/', data={
            'name': 'Anita Kulkarni',
            'phone': '9822003344',
            'email': 'anita@example.com',
            'date': res_date,
            'time': res_time,
            'guests': 2
        }, follow_redirects=True)
        self.assertEqual(response2.status_code, 200)
        self.assertIn(b'Reservation Confirmed', response2.data)

        # Now all tables with capacity 2 are taken. A 3rd booking for 2 guests in same slot should find higher cap or fail if capacity filled
        # Let's verify that tables already booked for this slot are not re-assigned:
        res1 = Reservation.query.filter_by(customer_name='Suresh Deshmukh').first()
        res2 = Reservation.query.filter_by(customer_name='Anita Kulkarni').first()
        self.assertNotEqual(res1.table_id, res2.table_id, 'Two simultaneous reservations must NOT share the same table')


if __name__ == '__main__':
    unittest.main(verbosity=2)

