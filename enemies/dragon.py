from copy import deepcopy
from .enemy import Enemy

SAVE_VERSION = 1

_ELEMENT_OPPOSITES = {
    "fire": "ice",
    "ice": "fire",
    "wind": "earth",
    "earth": "wind",
    "lightning": "water",
    "water": "lightning",
    "light": "dark",
    "dark": "light",
}

DEFAULT_ABILITIES = {
    "Dragonbreath": {
        "damage multiplier": 5,
        "chance": 0.1
    },
    "Wind Gust": {
        "damage multiplier": 3,
        "chance": 0.2
    },
    "Tail Whip": {
        "damage multiplier": 2,
        "chance": 0.3
    },
    "Claw": {
        "damage multiplier": 1,
        "chance": 0.4
    }
}

class Dragon(Enemy):
    def __init__(self, name, element="fire", abilities=None):
        super().__init__(name)
        self.element = element
        self.abilities = deepcopy(DEFAULT_ABILITIES if abilities is None else abilities)

    @staticmethod
    def element_relation(attack_element, target_element):
        if attack_element not in _ELEMENT_OPPOSITES:
            return "neutral"
        if target_element not in _ELEMENT_OPPOSITES:
            return "neutral"
        if target_element == _ELEMENT_OPPOSITES[attack_element]:
            return "weak"
        if target_element == attack_element:
            return "strong"
        return "neutral"

    def is_weak_to(self, attack_element):
        return self.element_relation(attack_element, self.element) == "weak"

    def is_strong_to(self, attack_element):
        return self.element_relation(attack_element, self.element) == "strong"

    def snapshot(self):
        return {
            "version": SAVE_VERSION,
            "name": self.name,
            "health": self.health,
            "element": self.element,
            "abilities": deepcopy(self.abilities),
        }

    def to_dict(self):
        return self.snapshot()

    def restore(self, snapshot):
        version = snapshot.get("version", SAVE_VERSION)
        if version != SAVE_VERSION:
            raise ValueError(f"unsupported save version: {version!r}")
        element = snapshot["element"]
        abilities = deepcopy(snapshot["abilities"])
        name = snapshot["name"]
        health = snapshot["health"]
        self._validate_restore_data(name, health, element, abilities)
        self.name = name
        self.health = health
        self.element = element
        self.abilities = abilities
        self.is_alive = self.health > 0
        return self

    def load(self, snapshot):
        return self.restore(snapshot)

    @classmethod
    def from_snapshot(cls, snapshot):
        version = snapshot.get("version", SAVE_VERSION)
        if version != SAVE_VERSION:
            raise ValueError(f"unsupported save version: {version!r}")
        element = snapshot["element"]
        abilities = deepcopy(snapshot["abilities"])
        name = snapshot["name"]
        health = snapshot["health"]
        cls._validate_restore_data(name, health, element, abilities)
        dragon = cls.__new__(cls)
        Enemy.__init__(dragon, snapshot["name"])
        dragon.element = element
        dragon.abilities = abilities
        dragon.health = health
        dragon.is_alive = dragon.health > 0
        return dragon

    @classmethod
    def from_dict(cls, snapshot):
        return cls.from_snapshot(snapshot)

    @staticmethod
    def _validate_restore_data(name, health, element, abilities):
        if not isinstance(name, str) or not name:
            raise ValueError("snapshot field 'name' must be a non-empty string")
        if not isinstance(health, int) or isinstance(health, bool) or health < 0:
            raise ValueError("snapshot field 'health' must be a non-negative integer")
        if element not in _ELEMENT_OPPOSITES:
            raise ValueError(f"unknown dragon element: {element!r}")
        if not isinstance(abilities, dict) or not abilities:
            raise ValueError("snapshot field 'abilities' must be a non-empty mapping")
        total_chance = 0
        for ability_name, ability in abilities.items():
            if not isinstance(ability_name, str) or not ability_name:
                raise ValueError("ability names must be non-empty strings")
            if not isinstance(ability, dict):
                raise ValueError(f"ability {ability_name!r} must be a mapping")
            multiplier = ability.get("damage multiplier")
            chance = ability.get("chance")
            if not isinstance(multiplier, (int, float)) or isinstance(multiplier, bool):
                raise ValueError(f"ability {ability_name!r} needs a numeric damage multiplier")
            if not isinstance(chance, (int, float)) or isinstance(chance, bool):
                raise ValueError(f"ability {ability_name!r} needs a numeric chance")
            if multiplier <= 0 or chance < 0:
                raise ValueError(f"ability {ability_name!r} has invalid multiplier or chance")
            total_chance += chance
        if abs(total_chance - 1) > 1e-9:
            raise ValueError("ability chances must sum to 1")
