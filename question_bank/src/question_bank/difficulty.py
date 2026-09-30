"""Canonical five-level Mathematics difficulty scale and pool compatibility."""

from __future__ import annotations

DIFFICULTY_LEVELS = (1, 2, 3, 4, 5)
DIFFICULTY_KEYS = tuple(str(level) for level in DIFFICULTY_LEVELS)
DIFFICULTY_DEFINITIONS = {
    "1": "Direct recall or one familiar taught step with little interpretation.",
    "2": "Routine application using one or two linked steps in a familiar representation.",
    "3": "Multi-step application or interpretation requiring a routine choice of method.",
    "4": "An unfamiliar problem requiring method selection, constraints, or justification.",
    "5": "Complex non-routine synthesis requiring several ideas, sustained reasoning, or proof.",
}

# Stage ranges overlap deliberately. They describe how an item is used in a lesson,
# while difficulty describes the mathematical demand. Level 3 remains a valid
# challenge stage so the immutable N1 pilot does not need to be re-keyed.
PRACTICE_STAGE_DIFFICULTIES = {
    "guided": frozenset({1, 2}),
    "independent": frozenset({2, 3, 4}),
    "challenge": frozenset({3, 4, 5}),
    "checkpoint": frozenset(DIFFICULTY_LEVELS),
    "adaptive": frozenset(DIFFICULTY_LEVELS),
}
