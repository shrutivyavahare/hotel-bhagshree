"""
Hotel Bhagshree — Rule-Based Food Recommendation Engine
=========================================================

Architecture: Knowledge-Based Expert System with Forward Chaining

This module implements a deterministic IF–THEN inference engine.
No ML, no LLMs, no external APIs — pure Python rule evaluation.

Components:
  1. KnowledgeBase    — loads & stores rules from SQLite
  2. WorkingMemory    — holds user's preference facts
  3. InferenceEngine  — forward-chaining rule evaluator
  4. RecommendationResult — structured output with explanation
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class UserPreferences:
    """Represents the user's input facts for the working memory."""
    food_type:   str             # 'vegetarian' | 'non_vegetarian'
    spice_level: str             # 'mild' | 'medium' | 'spicy' | 'extra_spicy'
    cuisine:     Optional[str]   # 'Maharashtrian' | 'Punjabi' | 'South Indian' | 'Chinese' | 'Any'
    budget:      float           # max budget in INR
    meal_time:   str             # 'breakfast' | 'lunch' | 'dinner' | 'snacks' | 'dessert'
    category:    Optional[str]   # 'Maharashtrian' | ... | 'Any'


@dataclass
class MatchedRule:
    """A rule that fired during forward chaining."""
    rule_id:    str
    rule_name:  str
    action:     str
    priority:   int
    conditions: dict
    matched_conditions: list = field(default_factory=list)


@dataclass
class DishRecommendation:
    """A single recommended dish with full justification."""
    dish_id:          int
    name:             str
    description:      str
    price:            float
    food_type:        str
    spice_level:      str
    category:         str
    image_file:       str
    prep_time:        int
    calories:         Optional[int]
    rating:           float
    matched_rules:    list   # list of MatchedRule
    explanation:      str
    confidence_score: float  # 0.0 – 1.0


@dataclass
class RecommendationResult:
    """Full output of one recommendation session."""
    recommendations:  list             # list[DishRecommendation]
    fired_rules:      list             # list[MatchedRule]
    user_preferences: UserPreferences
    total_rules_checked: int
    total_rules_fired:   int
    session_notes:    str = ''


# ── Knowledge Base ────────────────────────────────────────────────────────────

class KnowledgeBase:
    """
    Loads IF–THEN rules from the database and provides querying methods.
    Rules are cached in memory for performance.
    """

    def __init__(self):
        self._rules = []
        self._loaded = False

    def load_rules(self, rules_from_db: list) -> None:
        """Load and parse rules from database ORM objects."""
        self._rules = []
        for rule_obj in rules_from_db:
            try:
                conditions = json.loads(rule_obj.conditions)
                self._rules.append({
                    'rule_id':    rule_obj.rule_id,
                    'rule_name':  rule_obj.rule_name,
                    'conditions': conditions,
                    'action':     rule_obj.action,
                    'priority':   rule_obj.priority,
                    'is_active':  rule_obj.is_active,
                })
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"Skipping malformed rule {rule_obj.rule_id}: {e}")

        # Sort by priority descending (higher priority fires first)
        self._rules.sort(key=lambda r: r['priority'], reverse=True)
        self._loaded = True
        logger.info(f"KnowledgeBase loaded {len(self._rules)} rules.")

    def get_active_rules(self) -> list:
        return [r for r in self._rules if r.get('is_active', True)]

    def total_rules(self) -> int:
        return len(self._rules)


# ── Working Memory ────────────────────────────────────────────────────────────

class WorkingMemory:
    """
    Holds the set of facts derived from user preferences.
    The inference engine reads from and asserts new facts into working memory.
    """

    def __init__(self, preferences: UserPreferences):
        self.facts = {}
        self._assert_preferences(preferences)

    def _assert_preferences(self, prefs: UserPreferences) -> None:
        """Convert UserPreferences into a fact dictionary."""
        self.facts['food_type']   = prefs.food_type
        self.facts['spice_level'] = prefs.spice_level
        self.facts['meal_time']   = prefs.meal_time
        self.facts['budget']      = prefs.budget

        if prefs.cuisine and prefs.cuisine.lower() not in ('any', 'no preference', ''):
            self.facts['cuisine'] = prefs.cuisine

        if prefs.category and prefs.category.lower() not in ('any', 'no preference', ''):
            self.facts['category'] = prefs.category

    def assert_fact(self, key: str, value) -> None:
        self.facts[key] = value

    def get_fact(self, key: str, default=None):
        return self.facts.get(key, default)

    def __repr__(self):
        return f"WorkingMemory({self.facts})"


# ── Inference Engine ──────────────────────────────────────────────────────────

class InferenceEngine:
    """
    Forward-chaining inference engine.

    Algorithm:
      1. Assert user preferences into Working Memory.
      2. For each active rule (ordered by priority):
         a. Evaluate ALL conditions against Working Memory facts.
         b. If ALL conditions match → rule FIRES.
         c. Assert rule's action into Working Memory (for chaining).
      3. Collect all fired rules.
      4. Filter menu items that satisfy BOTH:
         - At least one fired rule's conditions
         - Hard constraints (vegetarian safety, availability, budget)
      5. Score and rank results.
      6. Return RecommendationResult.
    """

    # Hard constraint: spice level ordering for "at most X spicy" matching
    SPICE_ORDER = {'mild': 0, 'medium': 1, 'spicy': 2, 'extra_spicy': 3}

    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base

    def evaluate(self, preferences: UserPreferences, menu_items: list) -> RecommendationResult:
        """
        Main entry point. Runs forward chaining and returns recommendations.

        Args:
            preferences: UserPreferences — user's input
            menu_items:  list of MenuItem ORM objects (already filtered available)

        Returns:
            RecommendationResult
        """
        working_memory = WorkingMemory(preferences)
        rules = self.kb.get_active_rules()
        total_checked = len(rules)

        # ── Phase 1: Forward Chaining — Fire Rules ───────────────────────────
        fired_rules: list[MatchedRule] = []
        for rule in rules:
            matched, matched_conds = self._evaluate_rule(rule, working_memory)
            if matched:
                mr = MatchedRule(
                    rule_id=rule['rule_id'],
                    rule_name=rule['rule_name'],
                    action=rule['action'],
                    priority=rule['priority'],
                    conditions=rule['conditions'],
                    matched_conditions=matched_conds,
                )
                fired_rules.append(mr)
                # Assert the rule's action as a new fact (simple forward chain)
                working_memory.assert_fact(f'rule_fired_{rule["rule_id"]}', True)

        logger.info(f"InferenceEngine: {len(fired_rules)}/{total_checked} rules fired.")

        # ── Phase 2: Filter & Score Dishes ──────────────────────────────────
        dish_recommendations = []

        for item in menu_items:
            # Hard constraint 1: Vegetarian safety
            if preferences.food_type == 'vegetarian' and item.food_type == 'non_vegetarian':
                continue

            # Hard constraint 2: Availability
            if not item.is_available:
                continue

            # Hard constraint 3: Budget
            if item.price > preferences.budget:
                continue

            # Match fired rules to this dish
            item_matched_rules = []
            for rule in fired_rules:
                if self._dish_satisfies_rule(item, rule.conditions):
                    item_matched_rules.append(rule)

            if not item_matched_rules:
                continue

            # Compute confidence score
            score = self._compute_score(item, preferences, item_matched_rules)

            # Build explanation
            explanation = self._build_explanation(item, preferences, item_matched_rules)

            dish_recommendations.append(DishRecommendation(
                dish_id=item.id,
                name=item.name,
                description=item.description,
                price=item.price,
                food_type=item.food_type,
                spice_level=item.spice_level,
                category=item.category.name if item.category else '',
                image_file=item.image_file,
                prep_time=item.prep_time,
                calories=item.calories,
                rating=item.rating,
                matched_rules=item_matched_rules,
                explanation=explanation,
                confidence_score=score,
            ))

        # Sort by confidence score descending
        dish_recommendations.sort(key=lambda d: d.confidence_score, reverse=True)

        session_notes = ''
        if not dish_recommendations:
            session_notes = (
                'No exact matches found for your current preferences. '
                'Try broadening your criteria — for example, choose "Any Cuisine" '
                'or increase your budget.'
            )
        elif len(dish_recommendations) > 8:
            dish_recommendations = dish_recommendations[:8]

        return RecommendationResult(
            recommendations=dish_recommendations,
            fired_rules=fired_rules,
            user_preferences=preferences,
            total_rules_checked=total_checked,
            total_rules_fired=len(fired_rules),
            session_notes=session_notes,
        )

    # ── Rule Evaluation ────────────────────────────────────────────────────────

    def _evaluate_rule(self, rule: dict, wm: WorkingMemory) -> tuple[bool, list]:
        """
        Evaluate a single rule against working memory.

        Returns (matched: bool, matched_conditions: list[str])
        """
        conditions = rule.get('conditions', {})
        matched_conds = []

        for key, required_value in conditions.items():
            fact_value = wm.get_fact(key)

            if key == 'budget_min':
                if fact_value is None or float(fact_value) < float(required_value):
                    return False, []
                matched_conds.append(f'Budget ≥ ₹{required_value}')

            elif key == 'budget_max':
                if fact_value is None or float(fact_value) > float(required_value):
                    return False, []
                matched_conds.append(f'Budget ≤ ₹{required_value}')

            else:
                if fact_value is None:
                    return False, []
                if str(fact_value).lower() != str(required_value).lower():
                    return False, []
                matched_conds.append(f'{key.replace("_", " ").title()} = {required_value}')

        return True, matched_conds

    def _dish_satisfies_rule(self, item, conditions: dict) -> bool:
        """Check if a specific menu item satisfies a rule's conditions."""
        for key, required_value in conditions.items():
            if key == 'food_type':
                if item.food_type != required_value:
                    return False

            elif key == 'spice_level':
                if item.spice_level != required_value:
                    return False

            elif key == 'cuisine':
                if not item.category or item.category.name != required_value:
                    return False

            elif key == 'category':
                if not item.category or item.category.name != required_value:
                    return False

            elif key == 'meal_time':
                if required_value not in item.meal_times_list:
                    return False

            elif key == 'budget_min':
                if item.price < float(required_value):
                    return False

            elif key == 'budget_max':
                if item.price > float(required_value):
                    return False

        return True

    # ── Scoring ────────────────────────────────────────────────────────────────

    def _compute_score(self, item, prefs: UserPreferences, matched_rules: list) -> float:
        """
        Compute a normalised confidence score [0.0 – 1.0].

        Factors:
          - Number of matched rules (weighted by priority)
          - Exact spice match bonus
          - Cuisine match bonus
          - Budget fit (items far below budget score lower — overpriced already filtered)
          - Item rating
          - Featured item bonus
        """
        score = 0.0

        # Rule priority weight
        max_priority = 10.0
        for rule in matched_rules:
            score += (rule.priority / max_priority) * 0.4

        # Exact spice match
        if item.spice_level == prefs.spice_level:
            score += 0.2

        # Cuisine match
        if (prefs.cuisine and prefs.cuisine.lower() not in ('any', '')
                and item.category and item.category.name == prefs.cuisine):
            score += 0.15

        # Meal time match
        if prefs.meal_time in item.meal_times_list:
            score += 0.1

        # Rating bonus (max 0.1)
        score += (item.rating / 5.0) * 0.1

        # Featured bonus
        if item.is_featured:
            score += 0.05

        return min(round(score, 3), 1.0)

    # ── Explanation Builder ────────────────────────────────────────────────────

    def _build_explanation(self, item, prefs: UserPreferences, matched_rules: list) -> str:
        """Generate a human-readable explanation for why a dish was recommended."""
        parts = []

        if item.food_type == prefs.food_type:
            label = 'vegetarian' if prefs.food_type == 'vegetarian' else 'non-vegetarian'
            parts.append(f"Matches your {label} preference")

        if item.spice_level == prefs.spice_level:
            sl_label = item.spice_level.replace('_', ' ')
            parts.append(f"Spice level is {sl_label} as you prefer")

        if (prefs.cuisine and prefs.cuisine.lower() not in ('any', '')
                and item.category and item.category.name == prefs.cuisine):
            parts.append(f"Authentic {prefs.cuisine} cuisine")

        if prefs.meal_time in item.meal_times_list:
            parts.append(f"Perfect for {prefs.meal_time}")

        if item.price <= prefs.budget:
            parts.append(f"Within your ₹{prefs.budget:.0f} budget at ₹{item.price:.0f}")

        if item.is_featured:
            parts.append("Chef's special recommendation")

        rule_names = [r.rule_name for r in matched_rules[:2]]
        if rule_names:
            parts.append(f"Matched rules: {', '.join(rule_names)}")

        return '. '.join(parts) + '.' if parts else 'Recommended based on your preferences.'


# ── Public API ────────────────────────────────────────────────────────────────

def get_recommendations(preferences: UserPreferences, menu_items: list,
                         rules_from_db: list) -> RecommendationResult:
    """
    Convenience function. Creates a fresh KnowledgeBase + InferenceEngine
    and returns a RecommendationResult.

    Usage:
        prefs  = UserPreferences(...)
        items  = MenuItem.query.filter_by(is_available=True).all()
        rules  = RecommendationRule.query.filter_by(is_active=True).all()
        result = get_recommendations(prefs, items, rules)
    """
    kb = KnowledgeBase()
    kb.load_rules(rules_from_db)
    engine = InferenceEngine(kb)
    return engine.evaluate(preferences, menu_items)
