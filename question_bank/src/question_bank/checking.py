"""Deterministic checkers for the supported answer formats.

Learner input is untrusted. Nothing in this module evaluates code. Numbers are read
with anchored regular expressions. Algebraic answers are read by a small
recursive-descent parser whose only output is an exact polynomial, or a quotient of
two exact polynomials, with rational coefficients. Input length, bracket nesting,
powers, polynomial size and coefficient size are all bounded. Every malformed input
raises ``AnswerFormatError``, which ``check_answer`` reports as a normal format error.
"""

import json
import logging
import re
import unicodedata
from dataclasses import dataclass
from decimal import InvalidOperation
from fractions import Fraction
from math import gcd, isqrt

from .models import AlgebraicResponse, NumericResponse, Response

logger = logging.getLogger(__name__)

MAX_ANSWER_LENGTH = 200
MAX_NESTING_DEPTH = 8
MAX_EXPONENT = 20
MAX_DEGREE = 40
MAX_TERMS = 100
MAX_COEFFICIENT_BITS = 512
MAX_TERM_PRODUCTS = 10_000
MAX_SCIENTIFIC_EXPONENT = 50
MAX_PRIME_BASE = 10**9
MAX_PRIME_POWER = 64
MAX_PRIME_PRODUCT_BITS = 4096

EMPTY_MESSAGE = "Enter an answer before checking."
TOO_LONG_MESSAGE = f"Answers can be at most {MAX_ANSWER_LENGTH} characters long."
TOO_LARGE_MESSAGE = "This answer is too large to check. Simplify it and try again."
NUMBER_MESSAGE = "Enter a number, decimal, fraction, or percentage."
EXPRESSION_MESSAGE = "Enter an expression using numbers, letters, + - * / ^ and brackets."
EQUALS_MESSAGE = "Enter only the expression, without an equals sign."
COMMA_MESSAGE = "Use a decimal point, not a comma, and write numbers in expressions without separators."
NUMBER_PLACEMENT_MESSAGE = (
    "Write a number before a letter or bracket (2x, not x2), and use * between two numbers."
)
AMBIGUOUS_DIVISION_MESSAGE = "Use brackets to show what is divided, for example 3/(2a) or (3/2)a."
BRACKET_MESSAGE = "Check that every bracket is closed."
NESTING_MESSAGE = "This answer has too many brackets inside brackets."
POWER_MESSAGE = f"Powers must be whole numbers from 0 to {MAX_EXPONENT}."
POWER_OF_POWER_MESSAGE = "Use brackets for a power of a power, for example (x^2)^3."
DIVIDE_BY_ZERO_MESSAGE = "This answer divides by zero."
CONFIGURATION_MESSAGE = "This question's answer cannot be checked automatically. Please report it."


class AnswerFormatError(ValueError):
    """The submitted answer could not be parsed for the configured checker."""


class CheckerConfigurationError(RuntimeError):
    """An authored canonical or accepted answer could not be read by its own checker."""


# ---------------------------------------------------------------------------
# Text normalisation
# ---------------------------------------------------------------------------

_CHARACTER_MAP = str.maketrans(
    {
        # Minus signs and dashes that keyboards, phones and word processors produce.
        "\u2212": "-",  # minus sign
        "\u2010": "-",  # hyphen
        "\u2011": "-",  # non-breaking hyphen
        "\u2012": "-",  # figure dash
        "\u2013": "-",  # en dash
        "\ufe63": "-",  # small hyphen-minus
        "\uff0d": "-",  # full-width hyphen-minus
        "\uff0b": "+",  # full-width plus sign
        # Spaces, including the thin and no-break spaces used as digit separators.
        "\t": " ",
        "\n": " ",
        "\r": " ",
        "\u00a0": " ",  # no-break space
        "\u2007": " ",  # figure space
        "\u2008": " ",  # punctuation space
        "\u2009": " ",  # thin space
        "\u200a": " ",  # hair space
        "\u202f": " ",  # narrow no-break space
        "\u3000": " ",  # ideographic space
        # Invisible characters that copy and paste can add.
        "\u200b": None,  # zero-width space
        "\u200c": None,  # zero-width non-joiner
        "\u200d": None,  # zero-width joiner
        "\u2060": None,  # word joiner
        "\ufeff": None,  # byte-order mark
    }
)


def _ascii_digits(text: str) -> str:
    """Map decimal digits from any script, such as Thai digits, to ASCII digits."""

    if text.isascii():
        return text
    return "".join(
        str(unicodedata.decimal(character)) if character.isdecimal() else character
        for character in text
    )


def _normalise(text: str) -> str:
    return " ".join(_ascii_digits(text.translate(_CHARACTER_MAP)).split())


def _configured(read, *args):
    """Read an authored value; a failure is an authoring defect, not a learner error."""

    try:
        return read(*args)
    except (AnswerFormatError, ValueError, ZeroDivisionError) as exc:
        raise CheckerConfigurationError(f"Authored answer {args[0]!r} is invalid: {exc}") from exc


# ---------------------------------------------------------------------------
# Numbers
# ---------------------------------------------------------------------------

_DECIMAL = r"(?:\d+(?:\.\d*)?|\.\d+)"
_PLAIN_NUMBER = re.compile(_DECIMAL)
_SCIENTIFIC = re.compile(rf"(?P<mantissa>{_DECIMAL}) ?[eE] ?(?P<exponent>[+-]?\d{{1,4}})")
_FRACTION = re.compile(r"(?P<numerator>\d+) ?/ ?(?P<denominator>\d+)")
_MIXED_NUMBER = re.compile(r"(?P<whole>\d+) (?P<numerator>\d+) ?/ ?(?P<denominator>\d+)")
_GROUPED_NUMBER = re.compile(
    r"(?P<lead>\d{1,3})(?P<groups>(?P<separator>[, ])\d{3}(?:(?P=separator)\d{3})*)"
    r"(?P<decimals>\.\d+)?"
)


@dataclass(frozen=True)
class _Number:
    value: Fraction
    digits: str
    """The numeral without its sign, separators or unit, used for precision checks."""


def _decimal_fraction(text: str) -> Fraction:
    whole, _, decimals = text.partition(".")
    scale = 10 ** len(decimals)
    return Fraction(int(whole or "0") * scale + int(decimals or "0"), scale)


def _proper_fraction(numerator: str, denominator: str) -> Fraction:
    if int(denominator) == 0:
        raise AnswerFormatError("A fraction cannot have a denominator of zero.")
    return Fraction(int(numerator), int(denominator))


def _unsigned_number(text: str) -> _Number:
    if match := _MIXED_NUMBER.fullmatch(text):
        part = _proper_fraction(match["numerator"], match["denominator"])
        if part >= 1 or match["numerator"] == "0":
            raise AnswerFormatError(
                "Write a mixed number as a whole number and a proper fraction, such as 1 3/4."
            )
        return _Number(int(match["whole"]) + part, text)
    if match := _FRACTION.fullmatch(text):
        value = _proper_fraction(match["numerator"], match["denominator"])
        return _Number(value, f"{match['numerator']}/{match['denominator']}")
    if match := _GROUPED_NUMBER.fullmatch(text):
        digits = (
            match["lead"]
            + match["groups"].replace(match["separator"], "")
            + (match["decimals"] or "")
        )
        return _Number(_decimal_fraction(digits), digits)
    if match := _SCIENTIFIC.fullmatch(text):
        exponent = int(match["exponent"])
        if abs(exponent) > MAX_SCIENTIFIC_EXPONENT:
            raise AnswerFormatError(TOO_LARGE_MESSAGE)
        value = _decimal_fraction(match["mantissa"]) * Fraction(10) ** exponent
        return _Number(value, f"{match['mantissa']}e{exponent}")
    if _PLAIN_NUMBER.fullmatch(text):
        return _Number(_decimal_fraction(text), text)
    raise AnswerFormatError(NUMBER_MESSAGE)


def _read_number(text: str, *, allow_percent: bool = True) -> _Number:
    """Read a learner-typed number.

    Accepts integers, decimals, fractions, mixed numbers (``1 3/4``), scientific
    notation and digits grouped in threes with commas or spaces (``48,400``,
    ``48 400``). A trailing ``%`` divides by 100 unless the response declares ``%``
    as its unit (see ``_check_numeric``).
    """

    cleaned = _normalise(text)
    if len(cleaned) > MAX_ANSWER_LENGTH:
        raise AnswerFormatError(TOO_LONG_MESSAGE)
    scale = Fraction(1)
    if cleaned.endswith("%"):
        if not allow_percent:
            raise AnswerFormatError(NUMBER_MESSAGE)
        cleaned = cleaned[:-1].rstrip()
        scale = Fraction(1, 100)
    sign = 1
    if cleaned[:1] in {"+", "-"}:
        sign = -1 if cleaned[0] == "-" else 1
        cleaned = cleaned[1:].lstrip()
    number = _unsigned_number(cleaned)
    return _Number(sign * number.value * scale, number.digits)


def _fraction(value: str) -> Fraction:
    return _read_number(value).value


def _decimal_places(value: str) -> int:
    cleaned = value.strip().lower()
    if "e" in cleaned:
        coefficient, exponent = cleaned.split("e", 1)
        places = len(coefficient.partition(".")[2]) - int(exponent)
        return max(0, places)
    return len(cleaned.partition(".")[2])


def _significant_figures(value: str) -> int:
    cleaned = value.strip().lower().lstrip("+-")
    coefficient_text = cleaned.split("e", 1)[0]
    coefficient = coefficient_text.replace(".", "")
    coefficient = coefficient.lstrip("0")
    if "." not in coefficient_text and "e" not in cleaned:
        coefficient = coefficient.rstrip("0")
    return len(coefficient) if coefficient else 1


_PERCENT_LATEX = re.compile(r"(?P<number>[+-]?(?:\d+(?:\.\d+)?|\.\d+)) *(?:\\[,;:! ] *)?\\%")


def _displays_as_percentage(spec: NumericResponse) -> bool:
    """Whether the stored answer is a number of percent that is displayed with ``%``.

    This is a transitional inference for bank parts that predate an explicit
    ``unit: {"canonical": "%"}``. It applies only when ``canonical_latex`` is exactly
    the canonical number followed by ``\\%``, which is the answer the learner is shown.
    """

    match = _PERCENT_LATEX.fullmatch(spec.canonical_latex.strip())
    if match is None:
        return False
    try:
        return _read_number(match["number"]).value == _read_number(spec.canonical_answer).value
    except AnswerFormatError:
        return False


def _unit_spellings(spec: NumericResponse) -> tuple[str, ...]:
    if spec.unit is not None:
        return tuple(spec.unit.accepted)
    if _displays_as_percentage(spec):
        return ("%",)
    return ()


def _numeric_answer(text: str, units: tuple[str, ...]) -> _Number:
    """Read a number that may end with one of the response's accepted unit spellings.

    When the unit is ``%``, a trailing ``%`` is the unit and ``30%`` reads as 30,
    matching an answer stored as a number of percent. A unit is optional, as it was
    before units were read: ``unit.required`` is not enforced.
    """

    cleaned = _normalise(text)
    for unit in sorted(units, key=len, reverse=True):
        spelling = _normalise(unit)
        if not spelling:
            continue
        match = re.fullmatch(rf"(.*?) ?{re.escape(spelling)}", cleaned, re.IGNORECASE)
        if match is not None:
            return _read_number(match.group(1), allow_percent=False)
    return _read_number(cleaned)


def _check_numeric(spec: NumericResponse, answer: str) -> bool:
    units = _unit_spellings(spec)
    actual = _numeric_answer(answer, units)
    expected = _configured(_numeric_answer, spec.canonical_answer, units).value
    accepted = {_configured(_numeric_answer, item, units).value for item in spec.accepted_answers}
    if actual.value in accepted:
        return True
    if spec.comparison_mode == "absolute_tolerance":
        tolerance = _configured(_read_number, spec.absolute_tolerance).value
        return abs(actual.value - expected) <= tolerance
    if spec.comparison_mode == "rounded_dp":
        return actual.value == expected and _decimal_places(actual.digits) >= spec.rounding_precision
    if spec.comparison_mode == "rounded_sf":
        return (
            actual.value == expected
            and _significant_figures(actual.digits) == spec.rounding_precision
        )
    return actual.value == expected


# ---------------------------------------------------------------------------
# Prime factorisation, ordered lists, relations and ratios
# ---------------------------------------------------------------------------

_SUPERSCRIPT_DIGITS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
_SUPERSCRIPT_RUN = re.compile(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]+")
_SUPERSCRIPT_CHARACTERS = frozenset("⁰¹²³⁴⁵⁶⁷⁸⁹")
_PRIME_FACTOR = re.compile(r"(?P<base>\d{1,12})(?: ?\^ ?(?P<power>\d{1,4}|\(\d{1,4}\)))?")


def _is_prime(value: int) -> bool:
    if value < 2:
        return False
    return all(value % divisor for divisor in range(2, isqrt(value) + 1))


def _prime_factor_value(expression: str) -> int:
    text = _normalise(expression)
    for command in (r"\times", r"\cdot"):
        text = text.replace(command, "×")
    text = text.replace("{", "(").replace("}", ")").replace("**", "^")
    text = _SUPERSCRIPT_RUN.sub(lambda match: "^" + match[0].translate(_SUPERSCRIPT_DIGITS), text)
    product = 1
    size = 0
    for piece in re.split(r"[*×·⋅∙xX]", text):
        match = _PRIME_FACTOR.fullmatch(piece.strip())
        if match is None:
            raise AnswerFormatError("Use only prime factors, multiplication, and positive powers.")
        base = int(match["base"])
        power = int((match["power"] or "1").strip("()"))
        if power < 1 or power > MAX_PRIME_POWER:
            raise AnswerFormatError("Powers must be positive integers.")
        if base > MAX_PRIME_BASE:
            raise AnswerFormatError("Each prime factor must be smaller than one billion.")
        if not _is_prime(base):
            raise AnswerFormatError("Every factor base must be prime.")
        size += power * base.bit_length()
        if size > MAX_PRIME_PRODUCT_BITS:
            raise AnswerFormatError(TOO_LARGE_MESSAGE)
        product *= base**power
    return product


def _ordered_values(value: str) -> list[Fraction]:
    raw = _normalise(value)
    if raw.startswith("["):
        try:
            values = json.loads(raw)
        except json.JSONDecodeError:
            values = None
        if isinstance(values, list):
            return [_fraction(str(item)) for item in values]
    cleaned = raw.strip("[]()")
    separator = "," if "," in cleaned else "<" if "<" in cleaned else ">"
    if separator not in cleaned:
        raise AnswerFormatError("Separate the ordered values with commas or inequality signs.")
    return [_fraction(item) for item in cleaned.split(separator)]


RELATION = re.compile(r"^\s*(.+?)\s*(<=|>=|<|>|=)\s*(.+?)\s*$")
REVERSED_OPERATOR = {"<": ">", ">": "<", "<=": ">=", ">=": "<=", "=": "="}


def _relation(value: str):
    normalized = _normalise(value).replace("≤", "<=").replace("≥", ">=")
    match = RELATION.fullmatch(normalized)
    if not match:
        raise AnswerFormatError("Enter one complete relation, such as -2 < 3.")
    return _fraction(match.group(1)), match.group(2), _fraction(match.group(3))


def _ratio(value: str, terms: int) -> list[Fraction]:
    normalized = _normalise(value).lower().replace("\\colon", ":").replace("∶", ":")
    normalized = re.sub(r"\s+to\s+", ":", normalized)
    pieces = [piece.strip() for piece in normalized.split(":")]
    if len(pieces) != terms or any(not piece for piece in pieces):
        raise AnswerFormatError(f"Enter a ratio with {terms} terms separated by colons.")
    values = [_fraction(piece) for piece in pieces]
    if any(value <= 0 for value in values):
        raise AnswerFormatError("Ratio terms must be positive.")
    return values


def _is_simplest_integer_ratio(values: list[Fraction]) -> bool:
    if any(value.denominator != 1 for value in values):
        return False
    divisor = 0
    for value in values:
        divisor = gcd(divisor, abs(value.numerator))
    return divisor == 1


def _equivalent_ratio(actual: list[Fraction], expected: list[Fraction]) -> bool:
    return all(
        actual[index] * expected[0] == expected[index] * actual[0]
        for index in range(1, len(actual))
    )


# ---------------------------------------------------------------------------
# Algebraic expressions: tokens and syntax tree
# ---------------------------------------------------------------------------

_OPEN_BRACKETS = {"(": ")", "[": "]", "{": "}"}
_CLOSE_BRACKETS = set(_OPEN_BRACKETS.values())
_MULTIPLY_SIGNS = {"*", "×", "·", "⋅", "∙", "✕"}
_DIVIDE_SIGNS = {"/", "÷", "∕", "⁄"}
_LATEX_COMMANDS = {r"\times": "*", r"\cdot": "*", r"\div": "/"}
_NUMBER_TOKEN = re.compile(r"[0-9]+(?:\.[0-9]+)?|\.[0-9]+")
_ASCII_DIGITS = frozenset("0123456789")


@dataclass(frozen=True)
class _Token:
    kind: str  # number, letter, operator, power, open, close, end
    text: str


def _tokens(text: str) -> list[_Token]:
    tokens: list[_Token] = []
    index = 0
    while index < len(text):
        character = text[index]
        if character == " ":
            index += 1
        elif character in _ASCII_DIGITS or (
            character == "." and text[index + 1 : index + 2] in _ASCII_DIGITS
        ):
            match = _NUMBER_TOKEN.match(text, index)
            if match is None:
                raise AnswerFormatError(EXPRESSION_MESSAGE)
            index = match.end()
            if text[index : index + 1] in {".", *_ASCII_DIGITS}:
                raise AnswerFormatError(EXPRESSION_MESSAGE)
            tokens.append(_Token("number", match[0]))
        elif character.isascii() and character.isalpha():
            tokens.append(_Token("letter", character))
            index += 1
        elif character in "+-":
            tokens.append(_Token("operator", character))
            index += 1
        elif character == "*" and text.startswith("**", index):
            tokens.append(_Token("power", "^"))
            index += 2
        elif character in _MULTIPLY_SIGNS:
            tokens.append(_Token("operator", "*"))
            index += 1
        elif character in _DIVIDE_SIGNS:
            tokens.append(_Token("operator", "/"))
            index += 1
        elif character == "^":
            tokens.append(_Token("power", "^"))
            index += 1
        elif character in _SUPERSCRIPT_CHARACTERS:
            match = _SUPERSCRIPT_RUN.match(text, index)
            tokens.append(_Token("power", "^"))
            tokens.append(_Token("number", match[0].translate(_SUPERSCRIPT_DIGITS)))
            index = match.end()
        elif character in _OPEN_BRACKETS:
            tokens.append(_Token("open", character))
            index += 1
        elif character in _CLOSE_BRACKETS:
            tokens.append(_Token("close", character))
            index += 1
        elif character == "\\":
            for command, replacement in _LATEX_COMMANDS.items():
                if text.startswith(command, index):
                    tokens.append(_Token("operator", replacement))
                    index += len(command)
                    break
            else:
                raise AnswerFormatError(EXPRESSION_MESSAGE)
        elif character == "=":
            raise AnswerFormatError(EQUALS_MESSAGE)
        elif character == ",":
            raise AnswerFormatError(COMMA_MESSAGE)
        else:
            raise AnswerFormatError(EXPRESSION_MESSAGE)
    tokens.append(_Token("end", ""))
    return tokens


@dataclass(frozen=True)
class _Node:
    kind: str  # number, letter, neg, add, sub, mul, div, pow, group
    children: tuple["_Node", ...] = ()
    value: Fraction | None = None
    name: str = ""
    exponent: int = 0


class _Parser:
    """Recursive-descent parser for a restricted algebraic grammar.

    expression := [sign] term (("+" | "-") [sign] term)*
    term       := factor (("*" | "/") [sign] factor | factor)*   (juxtaposition multiplies)
    factor     := atom ["^" whole-number]
    atom       := number | letter | "(" expression ")"

    A single letter is one variable, so ``ab`` means a times b. A number may not follow
    a letter, a bracket or another number without an explicit ``*``. A division that is
    followed by juxtaposition (``3/2a``) is rejected as ambiguous.
    """

    def __init__(self, tokens: list[_Token], letters: frozenset[str]):
        self.tokens = tokens
        self.index = 0
        self.depth = 0
        self.letters = letters

    def peek(self) -> _Token:
        return self.tokens[self.index]

    def advance(self) -> _Token:
        token = self.tokens[self.index]
        if token.kind != "end":
            self.index += 1
        return token

    def parse(self) -> _Node:
        node = self.expression()
        token = self.peek()
        if token.kind == "close":
            raise AnswerFormatError(BRACKET_MESSAGE)
        if token.kind != "end":
            raise AnswerFormatError(EXPRESSION_MESSAGE)
        return node

    def signed_term(self) -> _Node:
        token = self.peek()
        if token.kind == "operator" and token.text in {"+", "-"}:
            self.advance()
            term = self.term()
            return _Node("neg", (term,)) if token.text == "-" else term
        return self.term()

    def expression(self) -> _Node:
        node = self.signed_term()
        while True:
            token = self.peek()
            if token.kind == "operator" and token.text in {"+", "-"}:
                self.advance()
                right = self.signed_term()
                node = _Node("add" if token.text == "+" else "sub", (node, right))
            else:
                return node

    def signed_factor(self) -> _Node:
        token = self.peek()
        if token.kind == "operator" and token.text in {"+", "-"}:
            self.advance()
            factor = self.factor()
            return _Node("neg", (factor,)) if token.text == "-" else factor
        return self.factor()

    def term(self) -> _Node:
        node = self.factor()
        after_division = False
        while True:
            token = self.peek()
            if token.kind == "operator" and token.text in {"*", "/"}:
                self.advance()
                right = self.signed_factor()
                node = _Node("mul" if token.text == "*" else "div", (node, right))
                after_division = token.text == "/"
            elif token.kind in {"letter", "open"}:
                if after_division:
                    raise AnswerFormatError(AMBIGUOUS_DIVISION_MESSAGE)
                node = _Node("mul", (node, self.factor()))
            elif token.kind == "number":
                raise AnswerFormatError(NUMBER_PLACEMENT_MESSAGE)
            else:
                return node

    def factor(self) -> _Node:
        node = self.atom()
        if self.peek().kind != "power":
            return node
        self.advance()
        exponent = self.exponent()
        if self.peek().kind == "power":
            raise AnswerFormatError(POWER_OF_POWER_MESSAGE)
        return _Node("pow", (node,), exponent=exponent)

    def exponent(self) -> int:
        token = self.advance()
        bracketed = token.kind == "open"
        if bracketed:
            token = self.advance()
        if token.kind != "number" or not token.text.isdigit() or len(token.text) > 3:
            raise AnswerFormatError(POWER_MESSAGE)
        if bracketed and self.advance().kind != "close":
            raise AnswerFormatError(POWER_MESSAGE)
        exponent = int(token.text)
        if exponent > MAX_EXPONENT:
            raise AnswerFormatError(POWER_MESSAGE)
        return exponent

    def atom(self) -> _Node:
        token = self.advance()
        if token.kind == "number":
            return _Node("number", value=_decimal_fraction(token.text))
        if token.kind == "letter":
            if token.text not in self.letters:
                raise AnswerFormatError(_letters_message(self.letters))
            return _Node("letter", name=token.text)
        if token.kind == "open":
            self.depth += 1
            if self.depth > MAX_NESTING_DEPTH:
                raise AnswerFormatError(NESTING_MESSAGE)
            inner = self.expression()
            closing = self.advance()
            if closing.kind != "close" or closing.text != _OPEN_BRACKETS[token.text]:
                raise AnswerFormatError(BRACKET_MESSAGE)
            self.depth -= 1
            return _Node("group", (inner,))
        if token.kind == "close" or (token.kind == "end" and self.depth):
            raise AnswerFormatError(BRACKET_MESSAGE)
        raise AnswerFormatError(EXPRESSION_MESSAGE)


def _letters_message(letters: frozenset[str]) -> str:
    names = sorted(letters)
    if not names:
        return "This answer should not contain letters."
    if len(names) == 1:
        return f"Use only the letter {names[0]}."
    return f"Use only the letters {', '.join(names[:-1])} and {names[-1]}."


def _parse_expression(text: str, letters: frozenset[str]) -> _Node:
    cleaned = _normalise(text)
    if not cleaned:
        raise AnswerFormatError(EXPRESSION_MESSAGE)
    if len(cleaned) > MAX_ANSWER_LENGTH:
        raise AnswerFormatError(TOO_LONG_MESSAGE)
    return _Parser(_tokens(cleaned), letters).parse()


# ---------------------------------------------------------------------------
# Exact polynomial arithmetic
# ---------------------------------------------------------------------------

Monomial = tuple[tuple[str, int], ...]
Polynomial = dict[Monomial, Fraction]
Rational = tuple[Polynomial, Polynomial]

_ONE: Polynomial = {(): Fraction(1)}


class _Budget:
    """Caps the total work of one evaluation, however the expression chains its products."""

    __slots__ = ("remaining",)

    def __init__(self):
        self.remaining = MAX_TERM_PRODUCTS

    def spend(self, amount: int) -> None:
        self.remaining -= amount
        if self.remaining < 0:
            raise AnswerFormatError(TOO_LARGE_MESSAGE)


def _bounded(polynomial: Polynomial) -> Polynomial:
    if len(polynomial) > MAX_TERMS:
        raise AnswerFormatError(TOO_LARGE_MESSAGE)
    for monomial, coefficient in polynomial.items():
        if sum(power for _, power in monomial) > MAX_DEGREE:
            raise AnswerFormatError(TOO_LARGE_MESSAGE)
        if (
            coefficient.numerator.bit_length() > MAX_COEFFICIENT_BITS
            or coefficient.denominator.bit_length() > MAX_COEFFICIENT_BITS
        ):
            raise AnswerFormatError(TOO_LARGE_MESSAGE)
    return polynomial


def _constant(value: Fraction) -> Polynomial:
    return _bounded({(): value}) if value else {}


def _add(left: Polynomial, right: Polynomial, sign: int = 1) -> Polynomial:
    result = dict(left)
    for monomial, coefficient in right.items():
        total = result.get(monomial, 0) + sign * coefficient
        if total:
            result[monomial] = total
        else:
            result.pop(monomial, None)
    return _bounded(result)


def _multiply_monomials(left: Monomial, right: Monomial) -> Monomial:
    powers = dict(left)
    for name, power in right:
        powers[name] = powers.get(name, 0) + power
    return tuple(sorted(powers.items()))


def _multiply(
    left: Polynomial, right: Polynomial, budget: _Budget | None = None, *, bounded: bool = True
) -> Polynomial:
    if budget is not None:
        budget.spend(len(left) * len(right))
    result: Polynomial = {}
    for left_monomial, left_coefficient in left.items():
        for right_monomial, right_coefficient in right.items():
            monomial = _multiply_monomials(left_monomial, right_monomial)
            total = result.get(monomial, 0) + left_coefficient * right_coefficient
            if total:
                result[monomial] = total
            else:
                result.pop(monomial, None)
    return _bounded(result) if bounded else result


def _scale(polynomial: Polynomial, factor: Fraction) -> Polynomial:
    return _bounded({monomial: value * factor for monomial, value in polynomial.items()})


def _fold_constant_denominator(numerator: Polynomial, denominator: Polynomial) -> Rational:
    if set(denominator) == {()}:
        return _scale(numerator, 1 / denominator[()]), _ONE
    return numerator, denominator


def _evaluate(node: _Node, budget: _Budget | None = None) -> Rational:
    budget = budget or _Budget()
    kind = node.kind
    if kind == "number":
        return _constant(node.value), _ONE
    if kind == "letter":
        return {((node.name, 1),): Fraction(1)}, _ONE
    if kind == "group":
        return _evaluate(node.children[0], budget)
    if kind == "neg":
        numerator, denominator = _evaluate(node.children[0], budget)
        return _scale(numerator, Fraction(-1)), denominator
    if kind == "pow":
        base = _evaluate(node.children[0], budget)
        if node.exponent == 0 and not base[0]:
            raise AnswerFormatError(POWER_MESSAGE)
        numerator, denominator = _ONE, _ONE
        for _ in range(node.exponent):
            numerator = _multiply(numerator, base[0], budget)
            denominator = _multiply(denominator, base[1], budget)
        return _fold_constant_denominator(numerator, denominator)
    left_numerator, left_denominator = _evaluate(node.children[0], budget)
    right_numerator, right_denominator = _evaluate(node.children[1], budget)
    if kind in {"add", "sub"}:
        sign = 1 if kind == "add" else -1
        if left_denominator == right_denominator:
            return _add(left_numerator, right_numerator, sign), left_denominator
        numerator = _add(
            _multiply(left_numerator, right_denominator, budget),
            _multiply(right_numerator, left_denominator, budget),
            sign,
        )
        return numerator, _multiply(left_denominator, right_denominator, budget)
    if kind == "mul":
        return _fold_constant_denominator(
            _multiply(left_numerator, right_numerator, budget),
            _multiply(left_denominator, right_denominator, budget),
        )
    if kind == "div":
        if not right_numerator:
            raise AnswerFormatError(DIVIDE_BY_ZERO_MESSAGE)
        return _fold_constant_denominator(
            _multiply(left_numerator, right_denominator, budget),
            _multiply(left_denominator, right_numerator, budget),
        )
    raise AssertionError(f"Unknown expression node {kind}")


def _equivalent(left: Rational, right: Rational) -> bool:
    """Exact equality of two rational functions, by cross-multiplication."""

    return _multiply(left[0], right[1], bounded=False) == _multiply(
        right[0], left[1], bounded=False
    )


def _degree(polynomial: Polynomial) -> int:
    return max((sum(power for _, power in monomial) for monomial in polynomial), default=0)


# ---------------------------------------------------------------------------
# Written form
# ---------------------------------------------------------------------------


def _without_brackets(node: _Node) -> _Node:
    while node.kind == "group":
        node = node.children[0]
    return node


def _summands(node: _Node, sign: int = 1) -> list[tuple[int, _Node]]:
    if node.kind == "add":
        return _summands(node.children[0], sign) + _summands(node.children[1], sign)
    if node.kind == "sub":
        return _summands(node.children[0], sign) + _summands(node.children[1], -sign)
    if node.kind == "neg":
        return _summands(node.children[0], -sign)
    return [(sign, node)]


def _factors(node: _Node) -> list[_Node]:
    if node.kind == "mul":
        return _factors(node.children[0]) + _factors(node.children[1])
    if node.kind == "neg":
        return _factors(node.children[0])
    return [node]


def _is_written_number(node: _Node) -> bool:
    """A number, or a bracketed signed number or numeric fraction such as (-3) or (1/2)."""

    node = _without_brackets(node)
    if node.kind == "neg":
        node = _without_brackets(node.children[0])
    if node.kind == "div":
        return all(_without_brackets(child).kind == "number" for child in node.children)
    return node.kind == "number"


def _is_reduced_fraction(numerator: Fraction, denominator: Fraction) -> bool:
    """Whether a written fraction uses whole numbers with no common factor (5/4, not 10/8)."""

    if numerator.denominator != 1 or denominator.denominator != 1 or denominator <= 0:
        return False
    return gcd(numerator.numerator, denominator.numerator) == 1


def _written_number_value(node: _Node) -> Fraction | None:
    """The value of a bracketed number such as (-3) or (1/2), or None for (2/4)."""

    node = _without_brackets(node)
    sign = 1
    if node.kind == "neg":
        sign = -1
        node = _without_brackets(node.children[0])
    if node.kind == "number":
        return sign * node.value
    numerator, denominator = (_without_brackets(child).value for child in node.children)
    if not _is_reduced_fraction(numerator, denominator):
        return None
    return sign * numerator / denominator


def _monomial_term(node: _Node) -> tuple[Fraction, Monomial] | None:
    """Read one written term such as 5x^2y, -x/4, (5x)/4 or (1/2)ab.

    Returns its coefficient and variable powers, or None when the term is not written
    as a single coefficient times distinct variable powers (``2*3x``, ``x*x``, ``x^0``
    and ``(x+1)`` are not). A written coefficient fraction must be in lowest terms, so
    ``2x/4``, ``(2x)/4`` and ``(2/4)x`` are not simplified terms. Brackets around a
    single term do not change how it is read.
    """

    coefficient = Fraction(1)
    numerators: list[Fraction] = []
    divisors: list[Fraction] = []
    bracketed_numbers = 0
    powers: dict[str, int] = {}
    pending = [node]
    while pending:
        current = pending.pop()
        if current.kind == "mul":
            pending.extend(current.children)
        elif current.kind == "neg":
            coefficient = -coefficient
            pending.append(current.children[0])
        elif current.kind == "div":
            divisor = _without_brackets(current.children[1])
            if divisor.kind != "number" or not divisor.value:
                return None
            divisors.append(divisor.value)
            coefficient /= divisor.value
            pending.append(current.children[0])
        elif current.kind == "number":
            numerators.append(current.value)
            coefficient *= current.value
        elif current.kind == "group" and _is_written_number(current):
            value = _written_number_value(current)
            if value is None:
                return None
            bracketed_numbers += 1
            coefficient *= value
        elif current.kind == "group" and len(_summands(_without_brackets(current))) == 1:
            pending.append(_without_brackets(current))
        elif current.kind == "letter" and current.name not in powers:
            powers[current.name] = 1
        elif (
            current.kind == "pow"
            and current.children[0].kind == "letter"
            and current.children[0].name not in powers
            and current.exponent >= 1
        ):
            powers[current.children[0].name] = current.exponent
        else:
            return None
    if len(numerators) + bracketed_numbers > 1 or len(divisors) > 1:
        return None
    if divisors:
        numerator = numerators[0] if numerators else Fraction(1)
        if bracketed_numbers or not _is_reduced_fraction(numerator, divisors[0]):
            return None
    return coefficient, tuple(sorted(powers.items()))


def _is_expanded(node: _Node) -> bool:
    """A sum of terms with like terms collected and no brackets, such as 6x^2+7x-20."""

    summands = _summands(_without_brackets(node))
    seen: set[Monomial] = set()
    for _, term in summands:
        read = _monomial_term(term)
        if read is None:
            return False
        coefficient, monomial = read
        if (coefficient == 0 and len(summands) > 1) or monomial in seen:
            return False
        seen.add(monomial)
    return True


def _contains_division(node: _Node) -> bool:
    return node.kind == "div" or any(_contains_division(child) for child in node.children)


def _bracket_content(factor: _Node) -> _Node | None:
    """The inside of a bracketed sum factor such as (x+2) or (x+2)^2."""

    if factor.kind == "pow":
        factor = factor.children[0]
    if factor.kind != "group":
        return None
    inner = _without_brackets(factor)
    return inner if len(_summands(inner)) > 1 else None


def _factor_multiplicity(factor: _Node) -> int:
    return factor.exponent if factor.kind == "pow" else 1


def _flat_factors(node: _Node) -> list[_Node]:
    """The factors of a product, opening brackets that hold only a product."""

    result = []
    for factor in _factors(_without_brackets(node)):
        inner = _without_brackets(factor)
        if factor.kind == "group" and len(_summands(inner)) == 1 and inner.kind in {"mul", "neg"}:
            result.extend(_flat_factors(inner))
        else:
            result.append(factor)
    return result


def _is_factorised(node: _Node) -> bool:
    """A product of at least two non-unit factors, at least one of them a bracketed sum.

    Each bracketed sum must itself be written with like terms collected.
    """

    node = _without_brackets(node)
    if node.kind == "neg":
        node = node.children[0]
    if _contains_division(node) or len(_summands(_without_brackets(node))) > 1:
        return False
    has_bracket = False
    multiplicity = 0
    for factor in _flat_factors(node):
        content = _bracket_content(factor)
        if content is not None:
            if not _is_expanded(content):
                return False
            has_bracket = True
            multiplicity += _factor_multiplicity(factor)
            continue
        read = _monomial_term(factor)
        if read is None:
            return False
        coefficient, monomial = read
        if monomial or abs(coefficient) != 1:
            multiplicity += _factor_multiplicity(factor) if monomial else 1
    return has_bracket and multiplicity >= 2


def _non_constant_factor_count(node: _Node) -> int:
    count = 0
    for factor in _flat_factors(node):
        if _bracket_content(factor) is not None:
            count += _factor_multiplicity(factor)
            continue
        read = _monomial_term(factor)
        if read is not None:
            count += sum(power for _, power in read[1])
    return count


def _is_primitive_irreducible_bracket(content: _Node) -> bool:
    polynomial, _ = _evaluate(content)
    coefficients = list(polynomial.values())
    if any(value.denominator != 1 for value in coefficients):
        return False
    divisor = 0
    for value in coefficients:
        divisor = gcd(divisor, value.numerator)
    if divisor != 1:
        return False
    letters = {name for monomial in polynomial for name, _ in monomial}
    for name in letters:
        if all(dict(monomial).get(name, 0) for monomial in polynomial):
            return False
    if len(letters) == 1 and _degree(polynomial) == 2:
        (name,) = letters
        a = polynomial.get(((name, 2),), Fraction(0)).numerator
        b = polynomial.get(((name, 1),), Fraction(0)).numerator
        c = polynomial.get((), Fraction(0)).numerator
        discriminant = b * b - 4 * a * c
        if discriminant >= 0 and isqrt(discriminant) ** 2 == discriminant:
            return False
    return True


def _is_factorised_completely(node: _Node, target: _Node) -> bool:
    """Factorised, with every bracket primitive and no fewer factors than the answer.

    A bracket is primitive when its coefficients are integers with no common factor and
    no letter divides every term. A one-letter quadratic bracket must also have no
    rational root.
    """

    if not _is_factorised(node):
        return False
    for factor in _flat_factors(node):
        content = _bracket_content(factor)
        if content is not None and not _is_primitive_irreducible_bracket(content):
            return False
    return _non_constant_factor_count(node) >= _non_constant_factor_count(target)


def _is_simplified_fraction(node: _Node, target: Rational) -> bool:
    """An expanded expression, or one fraction N/D in lowest terms.

    N and D are each expanded or factorised and contain no further division. Their
    coefficients are integers with no common factor, and D has no higher degree than the
    denominator of the authored answer, so no common factor remains.
    """

    if _is_expanded(node):
        return True
    node = _without_brackets(node)
    if node.kind == "neg":
        node = _without_brackets(node.children[0])
    if node.kind != "div":
        return _is_factorised(node)
    parts = [_without_brackets(child) for child in node.children]
    for part in parts:
        if _contains_division(part):
            return False
        if not (_is_expanded(part) or _is_factorised(part)):
            return False
    numerator, _ = _evaluate(parts[0])
    denominator, _ = _evaluate(parts[1])
    coefficients = [*numerator.values(), *denominator.values()]
    if any(value.denominator != 1 for value in coefficients):
        return False
    divisor = 0
    for value in coefficients:
        divisor = gcd(divisor, value.numerator)
    if divisor != 1:
        return False
    return _degree(denominator) <= _degree(target[1])


def _has_form(form: str, node: _Node, target_node: _Node, target_value: Rational) -> bool:
    if form == "any":
        return True
    if form == "expanded":
        return _is_expanded(node)
    if form == "factorised":
        return _is_factorised(node)
    if form == "factorised_completely":
        return _is_factorised_completely(node, target_node)
    if form == "simplified_fraction":
        return _is_simplified_fraction(node, target_value)
    raise CheckerConfigurationError(f"Unknown symbolic form {form!r}")


def _allowed_letters(spec: AlgebraicResponse) -> frozenset[str]:
    letters = set(spec.variables)
    for text in (spec.canonical_expression, *spec.accepted_equivalents):
        letters.update(character for character in text if character.isascii() and character.isalpha())
    return frozenset(letters)


def _read_expression(text: str, letters: frozenset[str]) -> tuple[_Node, Rational]:
    node = _parse_expression(text, letters)
    return node, _evaluate(node)


def _check_symbolic(spec: AlgebraicResponse, answer: str) -> bool:
    letters = _allowed_letters(spec)
    form = spec.checker_config.get("form", "any")
    node, value = _read_expression(answer, letters)
    for target in (spec.canonical_expression, *spec.accepted_equivalents):
        target_node, target_value = _configured(_read_expression, target, letters)
        if _equivalent(value, target_value) and _has_form(form, node, target_node, target_value):
            return True
    return False


def _check_expression(spec: AlgebraicResponse, answer: str) -> bool:
    if answer.strip() in spec.accepted_equivalents:
        return True
    if spec.comparison_mode == "symbolic_equivalence":
        return _check_symbolic(spec, answer)
    if spec.comparison_mode == "prime_factorisation":
        expected = _configured(_read_number, spec.canonical_expression).value
        return _prime_factor_value(answer) == expected
    if spec.comparison_mode == "ordered_numeric_list":
        expected = [
            _configured(_fraction, str(value)) for value in json.loads(spec.canonical_expression)
        ]
        actual = _ordered_values(answer)
        order = spec.checker_config["order"]
        correctly_ordered = actual == sorted(actual, reverse=order == "descending")
        return actual == expected and correctly_ordered
    if spec.comparison_mode == "exact_ratio":
        terms = spec.checker_config["terms"]
        actual = _ratio(answer, terms)
        expected = _configured(_ratio, spec.canonical_expression, terms)
        if spec.checker_config["require_simplest_integer_terms"]:
            return _is_simplest_integer_ratio(actual) and _equivalent_ratio(actual, expected)
        return _equivalent_ratio(actual, expected)
    if spec.comparison_mode == "exact_relation":
        actual_left, actual_op, actual_right = _relation(answer)
        expected_left, expected_op, expected_right = _configured(
            _relation, spec.canonical_expression
        )
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
    raise CheckerConfigurationError(f"Unsupported comparison mode {spec.comparison_mode!r}")


def check_answer(spec: Response, answer: str) -> dict:
    if not isinstance(answer, str) or not answer.strip():
        return {"correct": False, "error": EMPTY_MESSAGE}
    if len(answer) > MAX_ANSWER_LENGTH:
        return {"correct": False, "error": TOO_LONG_MESSAGE}
    try:
        correct = (
            _check_numeric(spec, answer)
            if isinstance(spec, NumericResponse)
            else _check_expression(spec, answer)
        )
        return {"correct": correct, "error": None}
    except CheckerConfigurationError:
        logger.exception("An authored answer specification failed its own checker")
        return {"correct": False, "error": CONFIGURATION_MESSAGE}
    except RecursionError:
        return {"correct": False, "error": TOO_LARGE_MESSAGE}
    except (AnswerFormatError, InvalidOperation, ValueError, ZeroDivisionError, OverflowError) as exc:
        return {"correct": False, "error": str(exc)}
