# Hotel Bhagshree — Restaurant Management & Expert Food Recommendation System

> **Award-Winning Dining Experience & Deterministic Rule-Based Food Recommendation Expert System**  
> *Handcrafted for Hotel Bhagshree, Nashik — Celebrating Authentic Indian Culinary Heritage Since 1995*

---

## 📖 Table of Contents
1. [Overview & Visual Design](#-overview--visual-design)
2. [Academic Feature: Rule-Based Recommendation Engine](#-academic-feature-rule-based-recommendation-engine)
3. [Technology Stack](#-technology-stack)
4. [Complete Project Structure](#-complete-project-structure)
5. [Local-First Installation & Quickstart](#-local-first-installation--quickstart)
6. [Database Models & Seeding](#-database-models--seeding)
7. [Default Credentials](#-default-credentials)
8. [Features & Modules](#-features--modules)
9. [Running Tests](#-running-tests)
10. [Academic Demonstration Guide](#-academic-demonstration-guide)

---

## 🎨 Overview & Visual Design

Hotel Bhagshree is a full-stack, local-first restaurant management and rule-based food recommendation web application. Built with high attention to UI/UX craft inspired by **Design No. 9**, it features:

- **Editorial Culinary Layout**: Warm cream and deep terracotta tones (`#1B120C`, `#FAF7F2`, `#8B2500`, `#C8963E`).
- **Typography Hierarchy**: Playfair Display serif paired with clean modern Inter sans-serif for legible menus and luxury aesthetics.
- **Local High-Resolution Photography**: Handcrafted food imagery for Maharashtrian, Punjabi, South Indian, Chinese, Snacks, Desserts, and Beverages.
- **Interactive Micro-Animations**: Smooth tab transitions, responsive drawer navigation, real-time cart drawer counters, and toast notifications.
- **100% Local-First Architecture**: Zero external AI cloud APIs, zero Firebase/Supabase dependencies; runs entirely offline on localhost.

---

## 🧠 Academic Feature: Rule-Based Recommendation Engine

The core computational intelligence component is a **deterministic Expert System** using **Forward Chaining** with **Conflict Resolution** and an **Explanation Generation Subsystem**.

### Architecture of the Recommendation Engine:
```
+--------------------------------------------------------------------------+
|                           User Preferences                               |
| (Food Type, Cuisine, Spice Level, Budget, Meal Time, Category)           |
+--------------------------------------------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
|                         Working Memory (Facts)                           |
+--------------------------------------------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
|                  Inference Engine (Forward Chaining)                     |
|  - Compares working facts with stored IF-THEN production rules           |
|  - Applies Conflict Resolution (Priority ordering & specificity score)  |
|  - Enforces Strict Safety Constraints (e.g., Vegetarian safety guard)    |
|  - Filters by Real-Time Availability & Budget limit                      |
+--------------------------------------------------------------------------+
                                     |
                                     v
+--------------------------------------------------------------------------+
|                   Explanation Facility & Output Delivery                 |
|  - Computes deterministic confidence score (0.0 to 1.0)                  |
|  - Generates natural language reasoning for each recommendation          |
|  - Returns matched rule identifiers (e.g. R001, R003) for audit          |
+--------------------------------------------------------------------------+
```

### Key Technical Properties:
1. **Deterministic Forward Chaining**: Matches user condition facts against antecedent conditions in the knowledge base.
2. **28 Active Production Rules**: Covers cuisine pairings, meal timings (Breakfast, Lunch, Dinner, Snacks), diet restrictions, spice profiles, and budget brackets.
3. **Strict Vegetarian Safety Invariant**: Non-vegetarian items are mathematically blocked from consideration when user specifies `vegetarian`.
4. **Transparent Explainability**: Users and academic evaluators can inspect exactly *which* rules fired and *why* a particular dish was recommended.
5. **Dynamic Knowledge Base Management**: Administrators can add, edit, toggle, or delete IF-THEN rules directly in the Admin Dashboard with changes persisting in SQLite.

---

## 💻 Technology Stack

- **Backend**: Python 3.9+ / Flask 3.0
- **Database & ORM**: SQLite 3 with Flask-SQLAlchemy 3.1 & SQLAlchemy 2.0
- **Authentication**: Flask-Login 0.6 with PBKDF2:SHA-256 secure password hashing
- **Frontend**: Semantic HTML5, Vanilla CSS3 (Custom Design System tokens), Vanilla ES6 JavaScript
- **Testing**: Python `unittest` test runner (24 comprehensive automated test cases)

---

## 📂 Complete Project Structure

```
hotel_bhagshree/
├── app/
│   ├── __init__.py                # Flask application factory, database initialization & seeding
│   ├── models.py                  # SQLAlchemy models (AdminUser, MenuItem, Category, Order, etc.)
│   ├── blueprints/
│   │   ├── __init__.py
│   │   ├── main.py                # Home, About, Contact routes
│   │   ├── menu.py                # Menu catalog, search, category & spice filters
│   │   ├── recommendation.py      # Recommendation UI & JSON API endpoint
│   │   ├── orders.py              # Cart session management, checkout, order tracking
│   │   ├── reservations.py        # Table booking & conflict prevention logic
│   │   ├── admin.py               # Admin dashboard, dishes/categories/rules/orders CRUD
│   │   └── auth.py                # Admin authentication (login, logout, session guards)
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css          # Design No. 9 design system & responsive styling
│   │   ├── js/
│   │   │   └── main.js            # Client-side interactions, cart state, modal handling
│   │   └── images/                # High-resolution local dish and restaurant photography
│   └── templates/
│       ├── base.html              # Core navigation, flash toasts, semantic footer
│       ├── index.html             # Hero, popular dishes, story, reviews, hours
│       ├── menu.html              # Filterable menu grid with live search & cart triggers
│       ├── recommendation.html    # Academic Expert System recommendation interface
│       ├── cart.html              # Shopping cart drawer/page with live totals & GST calculation
│       ├── checkout.html          # Order placement form with customer verification
│       ├── order_confirmation.html# Order confirmation with unique BHG reference
│       ├── order_status.html      # Order tracking page
│       ├── order_history.html     # Lookup previous orders by phone number
│       ├── reservations.html      # Table reservation calendar & time-slot selection
│       ├── reservation_confirmation.html # Booking voucher with table details
│       ├── about.html             # Heritage story, chef profile & photo gallery
│       ├── contact.html           # Location, operating hours, inquiry form & map
│       ├── auth/
│       │   └── login.html         # Elegant admin login screen
│       └── admin/
│           ├── dashboard.html     # Live metrics: revenue, order count, reservation count
│           ├── menu_list.html     # Dish catalog table with availability toggles
│           ├── menu_form.html     # Add / edit dish form
│           ├── categories.html    # Manage menu categories
│           ├── orders.html        # Live order management & status transitions
│           ├── reservations.html  # Reservation roster & status controls
│           └── rules_list.html    # IF-THEN recommendation rule manager
├── recommendation_engine/
│   └── __init__.py                # InferenceEngine, KnowledgeBase, Rule, UserPreferences
├── docs/
│   ├── ARCHITECTURE.md            # System architecture, schemas, and diagrams
│   └── RECOMMENDATION_SYSTEM.md   # Mathematical & logical explanation of expert system
├── tests/
│   ├── __init__.py
│   └── test_all.py                # 24 automated unit tests
├── requirements.txt               # Pinned Python package dependencies
├── run.py                         # Application runner
└── README.md                      # Comprehensive documentation
```

---

## 🚀 Local-First Installation & Quickstart

### Step 1: Clone or Navigate to Project
```bash
cd "hotel_bhagshree"
```

### Step 2: Create and Activate Virtual Environment
```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
python run.py
```

The application will start on **`http://localhost:5001`** and will automatically initialize the SQLite database with 26 menu items, 9 dining tables, and 28 IF-THEN rules on first boot.

---

## 🔑 Default Credentials

### Administrator Account
- **URL**: `http://localhost:5001/auth/login`
- **Username**: `admin`
- **Password**: `admin@123`

---

## 📊 Database Models & Seeding

The SQLite database (`bhagshree.db`) implements relational integrity:
1. `AdminUser`: Hashed password storage, session status, last login timestamp.
2. `Category`: 7 cuisines/types (Maharashtrian, Punjabi, South Indian, Chinese, Snacks, Desserts, Beverages).
3. `MenuItem`: Price in INR, food type (veg/non-veg), spice level (mild/medium/spicy/extra_spicy), availability flag, calories, prep time.
4. `ReservationTable`: Table number, capacity (2 to 10 guests), location (Window, Central, Private, Banquet).
5. `Reservation`: Date, time slot, guest count, table foreign key, customer contact, duplicate booking prevention.
6. `Order`: Unique `BHG` prefix ID, customer details, subtotal, 5% GST calculation, total amount, payment method, order status.
7. `OrderItem`: Order foreign key, menu item foreign key, unit price, quantity, line item subtotal.
8. `RecommendationRule`: Rule ID (R001–R028), JSON conditions, action text, priority, active toggle.

---

## 🧪 Running Tests

The test suite covers recommendation matching, safety constraints, budget filtering, order workflows, reservation conflicts, admin authentication, and database CRUD:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Output:
```text
test_login_failure (test_all.TestAdminAuth) ... ok
test_login_success (test_all.TestAdminAuth) ... ok
test_logout (test_all.TestAdminAuth) ... ok
test_protected_admin_route_redirect (test_all.TestAdminAuth) ... ok
test_gst_calculation (test_all.TestCartCalculations) ... ok
test_multi_item_subtotal (test_all.TestCartCalculations) ... ok
test_category_crud (test_all.TestDatabaseCRUD) ... ok
test_menu_item_crud_and_availability (test_all.TestDatabaseCRUD) ... ok
test_checkout_validation_phone_required (test_all.TestOrderCreation) ... ok
test_order_creation_flow (test_all.TestOrderCreation) ... ok
test_order_id_prefix (test_all.TestOrderIDGeneration) ... ok
test_order_ids_unique (test_all.TestOrderIDGeneration) ... ok
test_availability_filtering (test_all.TestRecommendationEngine) ... ok
test_budget_filtering (test_all.TestRecommendationEngine) ... ok
test_confidence_score_range (test_all.TestRecommendationEngine) ... ok
test_cuisine_rule_matching (test_all.TestRecommendationEngine) ... ok
test_explanation_generated (test_all.TestRecommendationEngine) ... ok
test_meal_time_matching (test_all.TestRecommendationEngine) ... ok
test_multiple_rules_fired (test_all.TestRecommendationEngine) ... ok
test_no_results_session_note (test_all.TestRecommendationEngine) ... ok
test_rule_priority_ordering (test_all.TestRecommendationEngine) ... ok
test_spice_level_matching (test_all.TestRecommendationEngine) ... ok
test_vegetarian_safety_constraint (test_all.TestRecommendationEngine) ... ok
test_reservation_creation_and_double_booking_prevention (test_all.TestReservationConflicts) ... ok

Ran 24 tests in 2.292s
OK
```

---

## 🎓 Academic Demonstration Guide

To showcase the Expert System during presentation or defense:
1. Navigate to **`http://localhost:5001/recommend`**.
2. Select **Diet: Vegetarian**, **Spice Level: Spicy**, **Cuisine: Maharashtrian**, **Budget: ₹200**, **Meal Time: Lunch**.
3. Click **Find My Recommendations**.
4. Observe the results:
   - **Recommended Dish**: *Misal Pav* (₹120).
   - **Confidence Score**: e.g., 95%.
   - **Fired Rules**: Shows `R001: Veg Spicy Maharashtrian Lunch` and `R022: Spicy Lover General`.
   - **Reasoning Explanation**: Explains why the dish satisfies the vegetarian, Maharashtrian, spicy, and budgetary constraints.
5. Demonstrate vegetarian security: change diet to **Vegetarian** and verify that no non-vegetarian dishes (like Chicken Kolhapuri or Butter Chicken) can ever appear, regardless of other parameters.
6. Open the Admin Panel (`/admin/rules`) to inspect or alter rules in real-time.
