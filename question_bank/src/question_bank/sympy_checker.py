"""Controlled symbolic equivalence checking for algebraic answers.

Untrusted learner input is never given to ``eval``, ``sympify`` or ``parse_expr``. A small
tokenizer and recursive-descent parser accept only school-algebra syntax (numbers, declared
variables, ``+ - * / ^``, brackets, implicit multiplication, superscript powers and common
Unicode operators) and build a syntax tree. That tree is first evaluated with exact rational
arithmetic at sample points that satisfy the declared domain constraints, which rejects almost
every wrong answer cheaply. SymPy then confirms equivalence exactly by cancelling the
difference to zero, under a time limit.

Optional form rules, selected by ``checker_config["form"]``:

``"factorised"``
    The answer must be a product (not a top-level sum). Every bracketed sum in it must be a
    polynomial with integer coefficients whose greatest common divisor is 1 and that is
    irreducible over the rationals, so ``(2x+2)(2x+8)`` or ``4(x^2+5x+4)`` is rejected while
    ``4(x+1)(x+4)`` is accepted.
``"simplified"``
    The answer must not be ``checker_config["original_expression"]`` itself. The comparison
    ignores spacing, brackets, explicit or implicit multiplication and the order of terms
    and factors.
"""

from __future__ import annotations

import random
import zlib
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from fractions import Fraction
from math import gcd

MAX_INPUT_LENGTH = 200
MAX_NUMBER_DIGITS = 12
MAX_EXPONENT = 12
MAX_DEGREE = 60
MAX_NODES = 200
CHECK_TIMEOUT_SECONDS = 2.0
SAMPLE_POINTS = 6
FORM_RULES = ("any", "factorised", "simplified")
CHECKER_CONFIG_KEYS = {"form", "original_expression"}


class AnswerFormatError(ValueError):
    """The submitted answer could not be parsed for the configured checker."""


class AnswerFormError(AnswerFormatError):
    """The answer has the right value but not the form the question asks for."""


# ---------------------------------------------------------------------------
# Syntax tree


@dataclass(frozen=True)
class Num:
    value: Fraction


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Group:
    """An expression written inside brackets; kept so form rules can see brackets."""

    body: object


@dataclass(frozen=True)
class Neg:
    operand: object


@dataclass(frozen=True)
class BinOp:
    op: str  # one of + - * /
    left: object
    right: object


@dataclass(frozen=True)
class Pow:
    base: object
    exponent: int


# ---------------------------------------------------------------------------
# Tokenizer

_TRANSLATIONS = str.maketrans(
    {
        "\u2212": "-",  # minus sign
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\ufe63": "-",
        "\uff0d": "-",
        "\uff0b": "+",
        "\u00d7": "*",  # multiplication sign
        "\u00b7": "*",  # middle dot
        "\u22c5": "*",  # dot operator
        "\u2217": "*",
        "\u2715": "*",
        "\u00f7": "/",  # division sign
        "\u2215": "/",
        "\u2044": "/",
        "\u00a0": " ",
        "\u2009": " ",
        "\u202f": " ",
        "\u3000": " ",
        "{": "(",
        "}": ")",
        "[": "(",
        "]": ")",
    }
)

_SUPERSCRIPTS = {
    "\u2070": "0",
    "\u00b9": "1",
    "\u00b2": "2",
    "\u00b3": "3",
    "\u2074": "4",
    "\u2075": "5",
    "\u2076": "6",
    "\u2077": "7",
    "\u2078": "8",
    "\u2079": "9",
    "\u207b": "-",
}


_DIGITS = "0123456789"
_DIGITS_SET = set(_DIGITS)


@dataclass(frozen=True)
class _Token:
    kind: str  # num, var, op, lparen, rparen, sup, end
    text: str
    position: int


def _normalise(text: str) -> str:
    return text.translate(_TRANSLATIONS).replace("**", "^")


def _tokenize(text: str, variables: tuple[str, ...]) -> list[_Token]:
    if len(text) > MAX_INPUT_LENGTH:
        raise AnswerFormatError(
            f"Your answer is too long. Use at most {MAX_INPUT_LENGTH} characters."
        )
    source = _normalise(text)
    by_length = sorted(variables, key=len, reverse=True)
    tokens: list[_Token] = []
    index = 0
    while index < len(source):
        char = source[index]
        if char.isspace():
            index += 1
            continue
        if char in _SUPERSCRIPTS:
            start = index
            while index < len(source) and source[index] in _SUPERSCRIPTS:
                index += 1
            digits = "".join(_SUPERSCRIPTS[item] for item in source[start:index])
            if not digits.lstrip("-").isdigit() or digits.count("-") > 1:
                raise AnswerFormatError("Write powers as whole numbers, such as x^2 or x².")
            tokens.append(_Token("sup", digits, start))
            continue
        if char in _DIGITS or (char == "." and source[index + 1 : index + 2] in _DIGITS_SET):
            start = index
            while index < len(source) and source[index] in _DIGITS:
                index += 1
            if index < len(source) and source[index] == ".":
                index += 1
                while index < len(source) and source[index] in _DIGITS:
                    index += 1
            literal = source[start:index]
            if len(literal.replace(".", "")) > MAX_NUMBER_DIGITS:
                raise AnswerFormatError("A number in your answer has too many digits.")
            if literal.count(".") > 1 or literal.endswith("."):
                raise AnswerFormatError(f"{literal!r} is not a valid number.")
            tokens.append(_Token("num", literal, start))
            continue
        if char.isalpha():
            start = index
            while index < len(source) and source[index].isalpha():
                index += 1
            word = source[start:index]
            position = 0
            while position < len(word):
                match = next((name for name in by_length if word.startswith(name, position)), None)
                if match is None:
                    raise AnswerFormatError(_unknown_symbol_message(word[position], variables))
                tokens.append(_Token("var", match, start + position))
                position += len(match)
            continue
        if char in "+-*/^":
            tokens.append(_Token("op", char, index))
            index += 1
            continue
        if char == "(":
            tokens.append(_Token("lparen", char, index))
            index += 1
            continue
        if char == ")":
            tokens.append(_Token("rparen", char, index))
            index += 1
            continue
        if char == "=":
            raise AnswerFormatError("Enter an expression, not an equation.")
        raise AnswerFormatError(f"The symbol {char!r} cannot be used in this answer.")
    tokens.append(_Token("end", "", len(source)))
    return tokens


def _unknown_symbol_message(symbol: str, variables: tuple[str, ...]) -> str:
    if not variables:
        return f"{symbol!r} is not used in this answer. Enter a number."
    names = sorted(variables)
    listed = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
    return f"{symbol!r} is not used in this answer. Use only {listed}."


# ---------------------------------------------------------------------------
# Parser


class _Parser:
    def __init__(self, tokens: list[_Token]):
        self.tokens = tokens
        self.index = 0
        self.nodes = 0

    @property
    def current(self) -> _Token:
        return self.tokens[self.index]

    def advance(self) -> _Token:
        token = self.tokens[self.index]
        self.index += 1
        return token

    def node(self, value):
        self.nodes += 1
        if self.nodes > MAX_NODES:
            raise AnswerFormatError("Your answer is too complicated to check.")
        return value

    def parse(self):
        if self.current.kind == "end":
            raise AnswerFormatError("Enter an expression.")
        tree = self.expression()
        if self.current.kind == "rparen":
            raise AnswerFormatError("There is a closing bracket without an opening bracket.")
        if self.current.kind != "end":
            raise AnswerFormatError("Check the expression; part of it could not be read.")
        return tree

    def expression(self):
        tree = self.term()
        while self.current.kind == "op" and self.current.text in "+-":
            op = self.advance().text
            tree = self.node(BinOp(op, tree, self.term()))
        return tree

    def term(self):
        tree = self.unary()
        while True:
            token = self.current
            if token.kind == "op" and token.text in "*/":
                self.advance()
                tree = self.node(BinOp(token.text, tree, self.unary()))
            elif token.kind in {"var", "lparen"}:
                # Implicit multiplication: 3x, xy, 2(x+1), (x+1)(x-1), x(x+2).
                tree = self.node(BinOp("*", tree, self.power()))
            elif token.kind == "num":
                raise AnswerFormatError(
                    "Put a multiplication sign before a number that follows a letter or bracket."
                )
            else:
                return tree

    def unary(self):
        if self.current.kind == "op" and self.current.text in "+-":
            op = self.advance().text
            operand = self.unary()
            return operand if op == "+" else self.node(Neg(operand))
        return self.power()

    def power(self):
        base = self.primary()
        while True:
            if self.current.kind == "sup":
                base = self.node(Pow(base, self._exponent_value(self.advance().text)))
            elif self.current.kind == "op" and self.current.text == "^":
                self.advance()
                base = self.node(Pow(base, self.exponent()))
            else:
                return base

    def exponent(self) -> int:
        sign = 1
        while self.current.kind == "op" and self.current.text in "+-":
            if self.advance().text == "-":
                sign = -sign
        if self.current.kind == "lparen":
            self.advance()
            value = self.exponent()
            if self.current.kind != "rparen":
                raise AnswerFormatError("A power is missing its closing bracket.")
            self.advance()
            return sign * value
        if self.current.kind != "num" or "." in self.current.text:
            raise AnswerFormatError("Powers must be whole numbers, such as x^2.")
        return self._exponent_value(str(sign * int(self.advance().text)))

    @staticmethod
    def _exponent_value(text: str) -> int:
        value = int(text)
        if abs(value) > MAX_EXPONENT:
            raise AnswerFormatError(f"Powers larger than {MAX_EXPONENT} are not supported.")
        return value

    def primary(self):
        token = self.current
        if token.kind == "num":
            self.advance()
            return self.node(Num(Fraction(token.text)))
        if token.kind == "var":
            self.advance()
            return self.node(Var(token.text))
        if token.kind == "lparen":
            self.advance()
            if self.current.kind == "rparen":
                raise AnswerFormatError("There is an empty pair of brackets.")
            body = self.expression()
            if self.current.kind != "rparen":
                raise AnswerFormatError("A bracket is not closed.")
            self.advance()
            return self.node(Group(body))
        if token.kind == "end":
            raise AnswerFormatError("The expression ends unexpectedly.")
        if token.kind == "rparen":
            raise AnswerFormatError("There is a closing bracket in an unexpected place.")
        if token.kind == "sup":
            raise AnswerFormatError("A power must follow a number, letter or bracket.")
        raise AnswerFormatError(f"{token.text!r} is in an unexpected place.")


def _degree(tree) -> int:
    if isinstance(tree, Num):
        return 0
    if isinstance(tree, Var):
        return 1
    if isinstance(tree, Group | Neg):
        return _degree(tree.body if isinstance(tree, Group) else tree.operand)
    if isinstance(tree, Pow):
        return abs(tree.exponent) * _degree(tree.base)
    left, right = _degree(tree.left), _degree(tree.right)
    return max(left, right) if tree.op in "+-" else left + right


def parse_expression(text: str, variables) -> object:
    """Parse ``text`` into a syntax tree that uses only ``variables``."""
    tree = _Parser(_tokenize(text, tuple(variables))).parse()
    if _degree(tree) > MAX_DEGREE:
        raise AnswerFormatError("Your answer is too complicated to check.")
    return tree


def free_variables(tree) -> set[str]:
    if isinstance(tree, Var):
        return {tree.name}
    if isinstance(tree, Num):
        return set()
    if isinstance(tree, Group):
        return free_variables(tree.body)
    if isinstance(tree, Neg):
        return free_variables(tree.operand)
    if isinstance(tree, Pow):
        return free_variables(tree.base)
    return free_variables(tree.left) | free_variables(tree.right)


# ---------------------------------------------------------------------------
# Domain constraints

_RELATIONS = ("!=", "<=", ">=", "<", ">")


@dataclass(frozen=True)
class Constraint:
    left: object
    relation: str
    right: object

    def holds(self, point: dict[str, Fraction]) -> bool:
        left = evaluate(self.left, point)
        right = evaluate(self.right, point)
        return {
            "!=": left != right,
            "<=": left <= right,
            ">=": left >= right,
            "<": left < right,
            ">": left > right,
        }[self.relation]


def parse_constraint(text: str, variables) -> Constraint:
    normalised = text.replace("\u2260", "!=").replace("\u2264", "<=").replace("\u2265", ">=")
    for relation in _RELATIONS:
        if relation in normalised:
            left, _, right = normalised.partition(relation)
            if any(other in right for other in _RELATIONS):
                break
            return Constraint(
                parse_expression(left, variables), relation, parse_expression(right, variables)
            )
    raise AnswerFormatError(
        f"Domain constraint {text!r} must have the form 'expression != value' or use <, <=, >, >=."
    )


# ---------------------------------------------------------------------------
# Exact rational evaluation (used to screen answers before SymPy)


def evaluate(tree, point: dict[str, Fraction]) -> Fraction:
    if isinstance(tree, Num):
        return tree.value
    if isinstance(tree, Var):
        return point[tree.name]
    if isinstance(tree, Group):
        return evaluate(tree.body, point)
    if isinstance(tree, Neg):
        return -evaluate(tree.operand, point)
    if isinstance(tree, Pow):
        return evaluate(tree.base, point) ** tree.exponent
    left = evaluate(tree.left, point)
    right = evaluate(tree.right, point)
    if tree.op == "+":
        return left + right
    if tree.op == "-":
        return left - right
    if tree.op == "*":
        return left * right
    return left / right


def _sample_points(variables, constraints, seed_text: str):
    generator = random.Random(zlib.crc32(seed_text.encode()))
    names = sorted(variables)
    for _ in range(SAMPLE_POINTS * 20):
        point = {
            name: Fraction(generator.randint(-97, 97), generator.randint(1, 13)) for name in names
        }
        try:
            if all(constraint.holds(point) for constraint in constraints):
                yield point
        except ZeroDivisionError:
            continue


def _numerically_equal(expected, actual, variables, constraints, seed_text: str) -> bool:
    compared = 0
    for point in _sample_points(variables, constraints, seed_text):
        try:
            expected_value = evaluate(expected, point)
        except ZeroDivisionError:
            continue
        try:
            actual_value = evaluate(actual, point)
        except ZeroDivisionError:
            # Undefined where the expected answer is defined and the domain allows it.
            return False
        if expected_value != actual_value:
            return False
        compared += 1
        if compared >= SAMPLE_POINTS:
            break
    return True


# ---------------------------------------------------------------------------
# SymPy conversion and time-limited confirmation

# SymPy runs on worker threads so a slow computation cannot hold a request open. Python cannot
# kill a thread, so the input limits above are what keep each computation small; the timeout
# bounds how long a learner waits.
_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="sympy-checker")


def run_with_timeout(function, *args, timeout: float = CHECK_TIMEOUT_SECONDS):
    future = _EXECUTOR.submit(function, *args)
    try:
        return future.result(timeout=timeout)
    except FutureTimeoutError as exc:
        future.cancel()
        raise AnswerFormatError(
            "Your answer took too long to check. Try writing it more simply."
        ) from exc


def to_sympy(tree, symbols: dict):
    import sympy

    if isinstance(tree, Num):
        return sympy.Rational(tree.value.numerator, tree.value.denominator)
    if isinstance(tree, Var):
        return symbols[tree.name]
    if isinstance(tree, Group):
        return to_sympy(tree.body, symbols)
    if isinstance(tree, Neg):
        return -to_sympy(tree.operand, symbols)
    if isinstance(tree, Pow):
        base = to_sympy(tree.base, symbols)
        if tree.exponent < 0 and base == 0:
            raise AnswerFormatError("Your answer divides by zero.")
        return base**tree.exponent
    left = to_sympy(tree.left, symbols)
    right = to_sympy(tree.right, symbols)
    if tree.op == "+":
        return left + right
    if tree.op == "-":
        return left - right
    if tree.op == "*":
        return left * right
    if right == 0:
        raise AnswerFormatError("Your answer divides by zero.")
    return left / right


def _symbols(variables) -> dict:
    import sympy

    # Symbols are created directly, so names such as E, I, N, O, Q or S stay plain variables.
    return {name: sympy.Symbol(name) for name in variables}


def _symbolically_equal(expected, actual, variables) -> bool:
    import sympy

    symbols = _symbols(variables)
    difference = sympy.cancel(
        sympy.together(to_sympy(expected, symbols) - to_sympy(actual, symbols))
    )
    if difference.has(sympy.zoo, sympy.nan, sympy.oo, -sympy.oo):
        raise AnswerFormatError("Your answer divides by zero.")
    return difference == 0


# ---------------------------------------------------------------------------
# Form rules


def _strip_groups(tree):
    while isinstance(tree, Group):
        tree = tree.body
    return tree


def _is_sum(tree) -> bool:
    return isinstance(tree, BinOp) and tree.op in "+-"


def _product_factors(tree, exponent: int = 1) -> list[tuple[object, int]]:
    """Flatten products, quotients, negation and powers into ``(base, exponent)`` pairs."""
    if isinstance(tree, Group) and not _is_sum(_strip_groups(tree)):
        return _product_factors(_strip_groups(tree), exponent)
    if isinstance(tree, Neg):
        return [(Num(Fraction(-1)), 1), *_product_factors(tree.operand, exponent)]
    if isinstance(tree, BinOp) and tree.op == "*":
        return _product_factors(tree.left, exponent) + _product_factors(tree.right, exponent)
    if isinstance(tree, BinOp) and tree.op == "/":
        return _product_factors(tree.left, exponent) + _product_factors(tree.right, -exponent)
    if isinstance(tree, Pow):
        return _product_factors(tree.base, exponent * tree.exponent)
    return [(tree, exponent)]


def _check_factorised(tree, variables) -> None:
    import sympy

    if _is_sum(_strip_groups(tree)):
        raise AnswerFormError("Your answer has the right value, but it is not factorised.")
    symbols = _symbols(variables)
    generators = [symbols[name] for name in sorted(variables)]
    for base, _ in _product_factors(tree):
        if not isinstance(base, Group):
            continue
        polynomial = to_sympy(base, symbols)
        try:
            poly = sympy.Poly(sympy.expand(polynomial), *generators, domain="QQ")
        except sympy.PolynomialError:
            poly = None
        coefficients = poly.coeffs() if poly is not None else []
        if poly is None or any(not coefficient.is_integer for coefficient in coefficients):
            raise AnswerFormError(
                "Your answer has the right value, but each bracket should contain whole-number "
                "coefficients."
            )
        divisor = 0
        for coefficient in coefficients:
            divisor = gcd(divisor, abs(int(coefficient)))
        if divisor != 1:
            raise AnswerFormError(
                "Your answer has the right value, but a common factor can still be taken out "
                "of a bracket."
            )
        if poly.total_degree() > 1 and not poly.is_irreducible:
            raise AnswerFormError(
                "Your answer has the right value, but a bracket can still be factorised."
            )


def structural_key(tree):
    """A key that ignores brackets, multiplication style and the order of terms or factors."""
    if isinstance(tree, Num):
        return ("num", tree.value)
    if isinstance(tree, Var):
        return ("var", tree.name)
    if isinstance(tree, Group):
        return structural_key(tree.body)
    if isinstance(tree, Neg):
        inner = _strip_groups(tree.operand)
        if isinstance(inner, Num):
            return ("num", -inner.value)
        return ("neg", structural_key(inner))
    if isinstance(tree, Pow):
        return ("pow", structural_key(tree.base), tree.exponent)
    if tree.op in "+-":
        terms = []
        _collect_terms(tree, terms)
        return ("add", tuple(sorted(terms, key=repr)))
    if tree.op == "*":
        factors = []
        _collect_factors(tree, factors)
        return ("mul", tuple(sorted(factors, key=repr)))
    return ("div", structural_key(tree.left), structural_key(tree.right))


def _collect_terms(tree, terms: list, negative: bool = False) -> None:
    tree = _strip_groups(tree)
    if isinstance(tree, BinOp) and tree.op in "+-":
        _collect_terms(tree.left, terms, negative)
        _collect_terms(tree.right, terms, negative != (tree.op == "-"))
        return
    key = structural_key(tree)
    if negative:
        key = ("num", -key[1]) if key[0] == "num" else ("neg", key)
    terms.append(key)


def _collect_factors(tree, factors: list) -> None:
    tree = _strip_groups(tree)
    if isinstance(tree, BinOp) and tree.op == "*":
        _collect_factors(tree.left, factors)
        _collect_factors(tree.right, factors)
        return
    factors.append(structural_key(tree))


# ---------------------------------------------------------------------------
# Public API


def validate_symbolic_config(
    canonical: str, variables, domain_constraints, checker_config: dict
) -> None:
    """Raise ``ValueError`` if a symbolic-equivalence response cannot be checked."""
    unknown = set(checker_config) - CHECKER_CONFIG_KEYS
    if unknown:
        raise ValueError(f"Unknown symbolic checker_config keys: {sorted(unknown)}")
    form = checker_config.get("form", "any")
    if form not in FORM_RULES:
        raise ValueError(f"checker_config.form must be one of {list(FORM_RULES)}")
    original = checker_config.get("original_expression")
    if form == "simplified":
        if not isinstance(original, str) or not original.strip():
            raise ValueError("The simplified form rule requires checker_config.original_expression")
    elif original is not None:
        raise ValueError("original_expression is only used with the simplified form rule")
    for name in variables:
        if not name or not name.isalpha():
            raise ValueError(f"Variable {name!r} must be made of letters")
    try:
        parse_expression(canonical, variables)
        for constraint in domain_constraints:
            parse_constraint(constraint, variables)
        if original is not None:
            parse_expression(original, variables)
    except AnswerFormatError as exc:
        raise ValueError(f"Symbolic checker cannot read the response: {exc}") from exc


def _strip_subject(answer: str, variables, canonical_tree) -> str:
    """Allow ``x = ...`` when ``x`` is a declared variable the expected answer is free of."""
    if "=" not in answer:
        return answer
    left, _, right = answer.partition("=")
    if "=" in right:
        raise AnswerFormatError("Enter one expression.")
    subject = left.strip()
    if subject in variables and subject not in free_variables(canonical_tree):
        return right
    raise AnswerFormatError("Enter an expression, not an equation.")


def check_symbolic_equivalence(
    answer: str,
    *,
    canonical: str,
    variables,
    domain_constraints=(),
    checker_config: dict | None = None,
    timeout: float = CHECK_TIMEOUT_SECONDS,
) -> bool:
    """Return whether ``answer`` equals ``canonical`` and has the configured form.

    Raises ``AnswerFormatError`` when the answer cannot be read, and ``AnswerFormError`` (a
    subclass) when its value is right but its form is not.
    """
    config = checker_config or {}
    variables = tuple(variables)
    expected = parse_expression(canonical, variables)
    actual = parse_expression(_strip_subject(answer, variables, expected), variables)
    constraints = [parse_constraint(item, variables) for item in domain_constraints]

    if not _numerically_equal(expected, actual, variables, constraints, canonical):
        return False
    if not run_with_timeout(_symbolically_equal, expected, actual, variables, timeout=timeout):
        return False

    form = config.get("form", "any")
    if form == "factorised":
        run_with_timeout(_check_factorised, actual, variables, timeout=timeout)
    elif form == "simplified":
        original = parse_expression(config["original_expression"], variables)
        if structural_key(actual) == structural_key(original):
            raise AnswerFormError(
                "That is the expression you started with. Simplify it to give your answer."
            )
    return True
