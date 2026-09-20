"""Deterministic checkers for the first supported answer formats."""

import ast
import json
import operator
import re
from decimal import InvalidOperation
from fractions import Fraction
from math import isqrt

from .models import AlgebraicResponse, NumericResponse, Response


class AnswerFormatError(ValueError):
    """The submitted answer could not be parsed for the configured checker."""


def _fraction(value: str) -> Fraction:
    cleaned = value.strip().replace("−", "-").replace(" ", "")
    if cleaned.endswith("%"):
        return _fraction(cleaned[:-1]) / 100
    try:
        return Fraction(cleaned)
    except (ValueError, ZeroDivisionError) as exc:
        raise AnswerFormatError("Enter a number, decimal, fraction, or percentage.") from exc


def _decimal_places(value: str) -> int:
    cleaned = value.strip().lower()
    if "e" in cleaned:
        coefficient, exponent = cleaned.split("e", 1)
        places = len(coefficient.partition(".")[2]) - int(exponent)
        return max(0, places)
    return len(cleaned.partition(".")[2])


def _significant_figures(value: str) -> int:
    cleaned = value.strip().lower().lstrip("+-")
    coefficient = cleaned.split("e", 1)[0].replace(".", "")
    coefficient = coefficient.lstrip("0")
    return len(coefficient) if coefficient else 1


def _is_prime(value: int) -> bool:
    if value < 2:
        return False
    return all(value % divisor for divisor in range(2, isqrt(value) + 1))


def _prime_factor_value(expression: str) -> int:
    normalized = expression.replace("×", "*").replace("·", "*").replace("^", "**")
    try:
        tree = ast.parse(normalized, mode="eval")
    except SyntaxError as exc:
        raise AnswerFormatError("Use multiplication and positive integer powers.") from exc

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and type(node.value) is int:
            if not _is_prime(node.value):
                raise AnswerFormatError("Every factor base must be prime.")
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
            return operator.mul(evaluate(node.left), evaluate(node.right))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            base = evaluate(node.left)
            if not isinstance(node.right, ast.Constant) or type(node.right.value) is not int:
                raise AnswerFormatError("Powers must be positive integers.")
            if node.right.value < 1:
                raise AnswerFormatError("Powers must be positive integers.")
            return base**node.right.value
        raise AnswerFormatError("Use only prime factors, multiplication, and positive powers.")

    return evaluate(tree)


def _ordered_values(value: str) -> list[Fraction]:
    cleaned = value.strip().strip("[]()")
    separator = "," if "," in cleaned else "<" if "<" in cleaned else ">"
    if separator not in cleaned:
        raise AnswerFormatError("Separate the ordered values with commas or inequality signs.")
    return [_fraction(item) for item in cleaned.split(separator)]


RELATION = re.compile(r"^\s*(.+?)\s*(<=|>=|<|>|=)\s*(.+?)\s*$")
REVERSED_OPERATOR = {"<": ">", ">": "<", "<=": ">=", ">=": "<=", "=": "="}


def _relation(value: str):
    normalized = value.replace("≤", "<=").replace("≥", ">=").replace("−", "-")
    match = RELATION.fullmatch(normalized)
    if not match:
        raise AnswerFormatError("Enter one complete relation, such as -2 < 3.")
    return _fraction(match.group(1)), match.group(2), _fraction(match.group(3))


def _check_numeric(spec: NumericResponse, answer: str) -> bool:
    actual = _fraction(answer)
    expected = _fraction(spec.canonical_answer)
    accepted = {_fraction(item) for item in spec.accepted_answers}
    if actual in accepted:
        return True
    if spec.comparison_mode == "absolute_tolerance":
        return abs(actual - expected) <= _fraction(spec.absolute_tolerance)
    if spec.comparison_mode == "rounded_dp":
        return actual == expected and _decimal_places(answer) >= spec.rounding_precision
    if spec.comparison_mode == "rounded_sf":
        return actual == expected and _significant_figures(answer) == spec.rounding_precision
    return actual == expected


def _check_expression(spec: AlgebraicResponse, answer: str) -> bool:
    if answer.strip() in spec.accepted_equivalents:
        return True
    if spec.comparison_mode == "prime_factorisation":
        return _prime_factor_value(answer) == int(_fraction(spec.canonical_expression))
    if spec.comparison_mode == "ordered_numeric_list":
        expected = [_fraction(str(value)) for value in json.loads(spec.canonical_expression)]
        actual = _ordered_values(answer)
        order = spec.checker_config["order"]
        correctly_ordered = actual == sorted(actual, reverse=order == "descending")
        return actual == expected and correctly_ordered
    if spec.comparison_mode == "exact_relation":
        actual_left, actual_op, actual_right = _relation(answer)
        expected_left, expected_op, expected_right = _relation(spec.canonical_expression)
        if actual_op not in spec.checker_config["allowed_operators"]:
            return False
        if (actual_left, actual_op, actual_right) == (expected_left, expected_op, expected_right):
            return True
        if spec.checker_config.get("allow_reversed_equivalent"):
            return (actual_left, actual_op, actual_right) == (
                expected_right,
                REVERSED_OPERATOR[expected_op],
                expected_left,
            )
        return False
    raise AnswerFormatError("Symbolic equivalence checking is not enabled in the N1 pilot.")


def check_answer(spec: Response, answer: str) -> dict:
    if not answer.strip():
        return {"correct": False, "error": "Enter an answer before checking."}
    try:
        correct = (
            _check_numeric(spec, answer)
            if isinstance(spec, NumericResponse)
            else _check_expression(spec, answer)
        )
        return {"correct": correct, "error": None}
    except (AnswerFormatError, InvalidOperation, ValueError) as exc:
        return {"correct": False, "error": str(exc)}
