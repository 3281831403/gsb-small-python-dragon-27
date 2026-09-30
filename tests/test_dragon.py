import unittest
from copy import deepcopy

from enemies.dragon import Dragon, DEFAULT_ABILITIES, SAVE_VERSION


ELEMENTS = ("fire", "ice", "wind", "earth", "lightning", "water", "light", "dark")

RELATION_CASES = [
    ("fire", "fire", "strong"),
    ("fire", "ice", "weak"),
    ("fire", "wind", "neutral"),
    ("ice", "fire", "weak"),
    ("ice", "ice", "strong"),
    ("ice", "earth", "neutral"),
    ("wind", "earth", "weak"),
    ("earth", "wind", "weak"),
    ("wind", "wind", "strong"),
    ("lightning", "water", "weak"),
    ("water", "lightning", "weak"),
    ("water", "water", "strong"),
    ("light", "dark", "weak"),
    ("dark", "light", "weak"),
    ("dark", "dark", "strong"),
    ("wind", "fire", "neutral"),
    (None, "fire", "neutral"),
    ("fire", None, "neutral"),
    ("nature", "fire", "neutral"),
    ("fire", "nature", "neutral"),
]


def ability_snapshot(damage=1, chance=1.0):
    return {"Bite": {"damage multiplier": damage, "chance": chance}}


INVALID_SNAPSHOT_CASES = [
    ("bad name", {"name": "", "health": 100, "element": "fire",
                  "abilities": ability_snapshot()}),
    ("float health", {"name": "Oolong", "health": 99.5, "element": "fire",
                      "abilities": ability_snapshot()}),
    ("negative health", {"name": "Oolong", "health": -1, "element": "fire",
                         "abilities": ability_snapshot()}),
    ("unknown element", {"name": "Oolong", "health": 100, "element": "nature",
                         "abilities": ability_snapshot()}),
    ("empty abilities", {"name": "Oolong", "health": 100, "element": "fire",
                         "abilities": {}}),
    ("bad multiplier", {"name": "Oolong", "health": 100, "element": "fire",
                        "abilities": {"Bite": {"damage multiplier": 0, "chance": 1.0}}}),
    ("bad chance", {"name": "Oolong", "health": 100, "element": "fire",
                    "abilities": {"Bite": {"damage multiplier": 1, "chance": -0.1}}}),
    ("chances sum", {"name": "Oolong", "health": 100, "element": "fire",
                     "abilities": {
                         "Bite": {"damage multiplier": 1, "chance": 0.4},
                         "Claw": {"damage multiplier": 1, "chance": 0.4}}}),
    ("wrong version", {"version": 999, "name": "Oolong", "health": 100,
                       "element": "fire", "abilities": ability_snapshot()}),
]


class ElementRelationTests(unittest.TestCase):
    def test_table_driven_relations(self):
        for attack_element, target_element, expected in RELATION_CASES:
            with self.subTest(attack=attack_element, target=target_element):
                self.assertEqual(
                    Dragon.element_relation(attack_element, target_element),
                    expected,
                )

    def test_all_element_pair_combinations(self):
        opposites = {
            "fire": "ice",
            "ice": "fire",
            "wind": "earth",
            "earth": "wind",
            "lightning": "water",
            "water": "lightning",
            "light": "dark",
            "dark": "light",
        }
        for attack_element in ELEMENTS:
            for target_element in ELEMENTS:
                relation = Dragon.element_relation(attack_element, target_element)
                if target_element == attack_element:
                    expected = "strong"
                elif opposites[attack_element] == target_element:
                    expected = "weak"
                else:
                    expected = "neutral"
                self.assertEqual(relation, expected)

    def test_instance_helpers(self):
        helper_cases = [
            ("fire", "ice", True, False),
            ("fire", "fire", False, True),
            ("wind", "fire", False, False),
            ("lightning", "water", True, False),
            ("nature", "fire", False, False),
        ]
        for attack_element, dragon_element, weak, strong in helper_cases:
            with self.subTest(element=dragon_element):
                dragon = Dragon("Oolong", element=dragon_element)
                self.assertIs(dragon.is_weak_to(attack_element), weak)
                self.assertIs(dragon.is_strong_to(attack_element), strong)

    def test_relation_is_deterministic(self):
        for _ in range(10):
            first = [Dragon.element_relation(a, t)
                     for a in ELEMENTS for t in ELEMENTS]
            second = [Dragon.element_relation(a, t)
                      for t in reversed(ELEMENTS) for a in reversed(ELEMENTS)]
            self.assertEqual(sorted(first), sorted(second))


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.dragon = Dragon("Oolong", element="ice")
        self.dragon.health = 42

    def test_snapshot_round_trip_restores_element(self):
        snapshot = self.dragon.snapshot()
        restored = Dragon("Placeholder", element="fire")
        restored.restore(snapshot)
        self.assertEqual(restored.name, "Oolong")
        self.assertEqual(restored.health, 42)
        self.assertEqual(restored.element, "ice")
        self.assertIs(restored.is_alive, True)
        self.assertEqual(restored.abilities, DEFAULT_ABILITIES)

    def test_snapshot_structure_is_table_driven(self):
        snapshot = self.dragon.snapshot()
        for field in ("version", "name", "health", "element", "abilities"):
            with self.subTest(field=field):
                self.assertIn(field, snapshot)
        self.assertEqual(snapshot["version"], SAVE_VERSION)

    def test_snapshot_is_deep_copy(self):
        snapshot = self.dragon.snapshot()
        snapshot["abilities"]["Claw"]["chance"] = 0.9
        snapshot["abilities"]["New Move"] = {"damage multiplier": 9, "chance": 0}
        self.assertEqual(self.dragon.abilities["Claw"]["chance"], 0.4)
        self.assertNotIn("New Move", self.dragon.abilities)

    def test_restored_abilities_are_deep_copied(self):
        snapshot = self.dragon.snapshot()
        restored = Dragon("Other").restore(snapshot)
        restored.abilities["Claw"]["chance"] = 0.8
        self.assertEqual(self.dragon.abilities["Claw"]["chance"], 0.4)
        self.assertEqual(snapshot["abilities"]["Claw"]["chance"], 0.4)

    def test_default_abilities_are_independent_copies(self):
        first = Dragon("First")
        second = Dragon("Second")
        self.assertIsNot(first.abilities, second.abilities)
        self.assertIsNot(first.abilities["Claw"], second.abilities["Claw"])
        first.abilities["Claw"]["chance"] = 0.99
        self.assertEqual(second.abilities["Claw"]["chance"], 0.4)
        self.assertEqual(DEFAULT_ABILITIES["Claw"]["chance"], 0.4)

    def test_custom_abilities_are_copied(self):
        custom = ability_snapshot()
        dragon = Dragon("Custom", abilities=custom)
        custom["Bite"]["chance"] = 0.5
        self.assertEqual(dragon.abilities["Bite"]["chance"], 1.0)

    def test_from_snapshot_builds_fresh_dragon(self):
        snapshot = self.dragon.snapshot()
        dragon = Dragon.from_snapshot(snapshot)
        self.assertEqual((dragon.name, dragon.health, dragon.element),
                         ("Oolong", 42, "ice"))
        dragon.abilities["Claw"]["chance"] = 0.2
        self.assertEqual(snapshot["abilities"]["Claw"]["chance"], 0.4)

    def test_alias_methods_round_trip(self):
        dragon = Dragon.from_dict(self.dragon.to_dict())
        dragon.load(self.dragon.snapshot())
        self.assertEqual(dragon.element, "ice")
        self.assertEqual(dragon.health, 42)


class RollbackTests(unittest.TestCase):
    def test_invalid_snapshots_roll_back_everything(self):
        for label, payload in INVALID_SNAPSHOT_CASES:
            with self.subTest(case=label):
                dragon = Dragon("Oolong", element="ice")
                dragon.health = 77
                before = deepcopy(dragon.snapshot())
                with self.assertRaises((ValueError, KeyError, TypeError)):
                    dragon.restore(payload)
                self.assertEqual(dragon.snapshot(), before)
                self.assertEqual(dragon.name, "Oolong")
                self.assertEqual(dragon.health, 77)
                self.assertEqual(dragon.element, "ice")

    def test_failure_does_not_pollute_later_restore(self):
        dragon = Dragon("Oolong", element="fire")
        bad = {"name": "Oolong", "health": 100, "element": "nature",
               "abilities": ability_snapshot()}
        with self.assertRaises(ValueError):
            dragon.restore(bad)
        good = Dragon("Windfang", element="wind")
        good.health = 55
        dragon.restore(good.snapshot())
        self.assertEqual(dragon.name, "Windfang")
        self.assertEqual(dragon.health, 55)
        self.assertEqual(dragon.element, "wind")

    def test_failed_input_snapshot_is_not_mutated(self):
        payload = {"name": "Oolong", "health": 100, "element": "nature",
                   "abilities": ability_snapshot()}
        payload_copy = deepcopy(payload)
        dragon = Dragon("Oolong")
        with self.assertRaises(ValueError):
            dragon.restore(payload)
        self.assertEqual(payload, payload_copy)

    def test_zero_health_marks_dead(self):
        dead_snapshot = self._dead_snapshot()
        dragon = Dragon("Oolong").restore(dead_snapshot)
        self.assertEqual(dragon.health, 0)
        self.assertIs(dragon.is_alive, False)

    @staticmethod
    def _dead_snapshot():
        snapshot = Dragon("Oolong", element="dark").snapshot()
        snapshot["health"] = 0
        return snapshot


if __name__ == "__main__":
    unittest.main()
