"""Content guardrails for authored questions and lessons.

The pre-review audits (``docs/plan/PRE_REVIEW_AUDIT_secondary_*.md``) found content defects
that every structural validator accepted: TAB characters left behind by an unescaped ``\\t``,
Python ``float`` reprs stored as canonical answers, math-identical questions hidden behind
different context sentences or encodings, plain-text mathematics, prompts with no task, hints
that state the answer and canonical answers that disagree with the worked solution.

Each check in this module returns :class:`ContentFinding` objects.  The validators turn them
into ``Issue`` rows whose severity comes from :class:`ContentLintPolicy`.  Every check starts
as a ``warning`` so existing content does not fail CI; the policy file documents how to
promote a check (globally or for one bank or course) to ``error`` once the content is clean.
See ``docs/plan/CONTENT_LINT_GUARDRAILS.md`` for the rules, the known limits and the
promotion procedure.

The heuristics are deliberately conservative: when an expression cannot be parsed with
certainty, the check stays silent rather than guessing.
"""

from __future__ import annotations

import math
import os
import re
import unicodedata
from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, model_validator

from .models import AlgebraicResponse, Model, NumericResponse, Question

Severity = Literal["warning", "error"]

POLICY_ENVIRONMENT_VARIABLE = "QUESTION_BANK_CONTENT_LINT_POLICY"
DEFAULT_POLICY_PATH = (
    Path(__file__).resolve().parents[3]
    / "backend_resources/question_bank/authoring/content-lint-policy-v1.json"
)


@dataclass(frozen=True)
class CheckSpec:
    code: str
    title: str
    description: str


CHECKS: dict[str, CheckSpec] = {
    spec.code: spec
    for spec in (
        CheckSpec(
            "content_control_character",
            "Control characters in learner-facing text",
            "TAB and other C0 control characters, newlines inside LaTeX, and double-escaped "
            "LaTeX commands such as '\\\\frac'. Usually an unescaped '\\t', '\\f', '\\b', "
            "'\\r' or '\\n' that swallowed the start of '\\times', '\\frac', '\\right' or "
            "'\\neq'.",
        ),
        CheckSpec(
            "content_float_noise",
            "Floating-point noise in answers",
            "Canonical or accepted answers written from a binary float repr, for example "
            "3.333333333333332, 4.000000000000002 or an exact answer stored as 15.0.",
        ),
        CheckSpec(
            "content_math_duplicate",
            "Math-identical questions or lesson examples",
            "Two items whose mathematical core (numbers, variables, operations, concept and "
            "answer) is identical once context sentences are removed and LaTeX and plain-text "
            "notation are normalised to one form.",
        ),
        CheckSpec(
            "content_plain_text_math",
            "Plain-text mathematics in text blocks",
            "Text blocks containing sqrt(...), ^ exponents, ASCII relations such as <= or !=, "
            "'*' multiplication, bracketed slash fractions or raw LaTeX commands, which should "
            "be inline_math or display_math blocks.",
        ),
        CheckSpec(
            "content_prompt_without_question",
            "Prompt with no question or instruction",
            "The learner-visible prompt (stem plus part prompt, or a lesson example/recall "
            "prompt) has no question mark and no instruction verb.",
        ),
        CheckSpec(
            "content_hint_reveals_answer",
            "Hint states the final answer",
            "A hint states the canonical answer as a result (after '=', 'is', 'gives', "
            "'make(s)', a box or a closing arrow), repeats an exact non-integer answer, or "
            "contains the full canonical expression.",
        ),
        CheckSpec(
            "content_answer_solution_mismatch",
            "Canonical answer disagrees with the worked solution",
            "The final value reached by the worked solution differs from the canonical answer, "
            "the final value does not satisfy an equation the solution solved, a purely "
            "numerical equality in the solution is false, or a 1/0 decision contradicts the "
            "two values the solution compares.",
        ),
    )
}
CONTENT_LINT_CODES = frozenset(CHECKS)


def is_content_lint_code(code: str) -> bool:
    """Return whether a (possibly prefixed) issue code comes from this module."""

    return code in CONTENT_LINT_CODES or any(
        code.endswith(f"_{item}") for item in CONTENT_LINT_CODES
    )


@dataclass(frozen=True)
class ContentFinding:
    code: str
    subject: str
    location: str
    message: str

    def render(self) -> str:
        if not self.location or self.location in self.message:
            return self.message
        return f"{self.location}: {self.message}"


# --------------------------------------------------------------------------------------------
# Severity policy
# --------------------------------------------------------------------------------------------


class CheckPolicy(Model):
    severity: Severity = "warning"
    error_scopes: list[str] = Field(default_factory=list)
    notes: str | None = None

    @model_validator(mode="after")
    def scopes_are_unique(self):
        if len(set(self.error_scopes)) != len(self.error_scopes):
            raise ValueError("error_scopes must be unique")
        return self


class ContentLintPolicy(Model):
    schema_version: Literal["1.0.0"] = "1.0.0"
    description: str | None = None
    checks: dict[str, CheckPolicy] = Field(default_factory=dict)

    @model_validator(mode="after")
    def checks_are_known(self):
        unknown = set(self.checks) - CONTENT_LINT_CODES
        if unknown:
            raise ValueError(f"Unknown content-lint checks: {sorted(unknown)}")
        return self

    def severity(self, code: str, scopes: Iterable[str] = ()) -> Severity:
        """Severity of ``code`` for content identified by ``scopes``.

        ``scopes`` holds the identifiers of the content, for example the bank key and
        stable key of a question, or the course key and lesson key of a lesson.  A check
        is an error when its global severity is ``error`` or when any scope matches an
        ``error_scopes`` entry exactly or as a prefix ending in ``*``.
        """

        policy = self.checks.get(code)
        if policy is None:
            return "warning"
        if policy.severity == "error":
            return "error"
        for scope in scopes:
            for pattern in policy.error_scopes:
                if pattern.endswith("*"):
                    if scope.startswith(pattern[:-1]):
                        return "error"
                elif scope == pattern:
                    return "error"
        return "warning"


_POLICY_CACHE: dict[tuple[str, float], ContentLintPolicy] = {}


def load_policy(path: Path | None = None) -> ContentLintPolicy:
    """Load the severity policy.

    Resolution order: explicit ``path``, the ``QUESTION_BANK_CONTENT_LINT_POLICY``
    environment variable, then the repository default.  A missing default file means
    every check is a warning.  An invalid policy file raises ``ValueError`` so a broken
    promotion cannot silently downgrade checks.
    """

    candidate = path or (
        Path(os.environ[POLICY_ENVIRONMENT_VARIABLE])
        if os.environ.get(POLICY_ENVIRONMENT_VARIABLE)
        else DEFAULT_POLICY_PATH
    )
    if not candidate.is_file():
        if path is not None or os.environ.get(POLICY_ENVIRONMENT_VARIABLE):
            raise ValueError(f"Content-lint policy {candidate} does not exist")
        return ContentLintPolicy()
    key = (str(candidate.resolve()), candidate.stat().st_mtime)
    cached = _POLICY_CACHE.get(key)
    if cached is not None:
        return cached
    try:
        policy = ContentLintPolicy.model_validate_json(candidate.read_text())
    except (OSError, ValidationError) as exc:
        raise ValueError(f"Invalid content-lint policy {candidate}: {exc}") from exc
    _POLICY_CACHE[key] = policy
    return policy


# --------------------------------------------------------------------------------------------
# Content traversal
# --------------------------------------------------------------------------------------------

_SKIPPED_KEYS = {"provenance", "generation_spec", "sha256", "path", "asset_key", "stable_key"}
_LATEX_KEYS = {
    "latex",
    "canonical_latex",
    "canonical_expression",
    "canonical_answer",
    "accepted_answers",
    "accepted_equivalents",
    "title",
}


def _walk_strings(value, location: str = "") -> Iterator[tuple[str, str, str]]:
    """Yield (location, key, string) for every string in a model dump."""

    if isinstance(value, dict):
        for key, item in value.items():
            if key in _SKIPPED_KEYS:
                continue
            child = f"{location}.{key}" if location else key
            if isinstance(item, str):
                yield child, key, item
            else:
                yield from _walk_strings(item, child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            child = f"{location}[{index}]"
            if isinstance(item, str):
                parent_key = location.rsplit(".", 1)[-1]
                yield child, parent_key, item
            else:
                yield from _walk_strings(item, child)


def _block_text(block) -> str:
    return getattr(block, "text", None) or getattr(block, "latex", None) or ""


def _blocks_text(blocks) -> str:
    return " ".join(_block_text(block) for block in blocks)


# --------------------------------------------------------------------------------------------
# Check: control characters
# --------------------------------------------------------------------------------------------

_CONTROL = re.compile(r"[\x00-\x09\x0b-\x1f\x7f]")
_ESCAPE_NAMES = {
    "\t": ("TAB", "\\t"),
    "\x08": ("backspace", "\\b"),
    "\x0c": ("form feed", "\\f"),
    "\r": ("carriage return", "\\r"),
    "\x07": ("bell", "\\a"),
    "\x0b": ("vertical tab", "\\v"),
    "\n": ("newline", "\\n"),
}
_DOUBLE_ESCAPED_COMMAND = re.compile(
    r"(?<!\\)\\\\(frac|dfrac|tfrac|times|sqrt|text|cdot|div|left|right|pi|leq?|geq?|neq|"
    r"approx|boxed|circ|quad|qquad|Rightarrow|implies|mathrm)(?![A-Za-z])"
)


def _control_message(text: str, match: re.Match) -> str:
    character = match.group()
    name, escape = _ESCAPE_NAMES.get(character, (f"U+{ord(character):04X}", None))
    following = re.match(r"[A-Za-z]+", text[match.end() :])
    context = text[max(0, match.start() - 12) : match.end() + 12]
    if escape and following:
        intended = escape + following.group()
        return (
            f"{name} character before '{following.group()}' "
            f"(probably '{intended}' written with an unescaped '{escape}') in {context!r}"
        )
    return f"{name} character in {context!r}"


def control_character_findings(document: dict, subject: str) -> list[ContentFinding]:
    messages: list[str] = []
    for location, key, text in _walk_strings(document):
        for match in _CONTROL.finditer(text):
            if match.group() == "\n" and key not in _LATEX_KEYS:
                continue
            messages.append(f"{location}: {_control_message(text, match)}")
        if key in _LATEX_KEYS:
            for match in _DOUBLE_ESCAPED_COMMAND.finditer(text):
                context = text[max(0, match.start() - 12) : match.end() + 12]
                messages.append(
                    f"{location}: double-escaped LaTeX command '\\\\{match.group(1)}' renders "
                    f"as a line break followed by the letters '{match.group(1)}' in {context!r}"
                )
    if not messages:
        return []
    return [
        ContentFinding(
            "content_control_character",
            subject,
            messages[0].split(":", 1)[0],
            _summarise(messages),
        )
    ]


def _summarise(messages: list[str], limit: int = 3) -> str:
    shown = "; ".join(messages[:limit])
    if len(messages) > limit:
        shown += f"; and {len(messages) - limit} more"
    return f"{len(messages)} occurrence(s): {shown}"


# --------------------------------------------------------------------------------------------
# Check: floating-point noise
# --------------------------------------------------------------------------------------------

_DECIMAL = re.compile(r"(?<![\d.])-?\d+\.(\d+)(?![\d.])")
_FLOAT_RUN = re.compile(r"(0{5,}|9{5,}|([1-8])\2{5,})\d{0,2}$")


def _is_float_noise(fraction_digits: str, *, threshold: int = 10) -> bool:
    if len(fraction_digits) >= threshold:
        return True
    return len(fraction_digits) >= 7 and _FLOAT_RUN.search(fraction_digits) is not None


def _answer_fields(response) -> list[tuple[str, str]]:
    if isinstance(response, NumericResponse):
        return [
            ("canonical_answer", response.canonical_answer),
            ("canonical_latex", response.canonical_latex),
            *(
                (f"accepted_answers[{index}]", value)
                for index, value in enumerate(response.accepted_answers)
            ),
        ]
    return [
        ("canonical_expression", response.canonical_expression),
        ("canonical_latex", response.canonical_latex),
        *(
            (f"accepted_equivalents[{index}]", value)
            for index, value in enumerate(response.accepted_equivalents)
        ),
    ]


def _response_float_messages(response, location: str) -> list[str]:
    messages = []
    for field_name, value in _answer_fields(response):
        for match in _DECIMAL.finditer(value):
            if _is_float_noise(match.group(1)):
                messages.append(
                    f"{location}.response.{field_name} = {value!r} looks like a binary "
                    "float repr; store the exact value or state the rounding"
                )
                break
    if (
        isinstance(response, NumericResponse)
        and response.comparison_mode == "exact_numeric"
        and re.fullmatch(r"-?\d+\.0+", response.canonical_answer)
    ):
        messages.append(
            f"{location}.response.canonical_answer = {response.canonical_answer!r} is an "
            "integer stored as a float; store the integer"
        )
    return messages


def float_noise_findings(
    responses: Iterable[tuple[str, object]],
    visible_text: Iterable[tuple[str, str]],
    subject: str,
) -> list[ContentFinding]:
    messages: list[str] = []
    for location, response in responses:
        messages.extend(_response_float_messages(response, location))
    for location, text in visible_text:
        for match in _DECIMAL.finditer(text):
            if _is_float_noise(match.group(1), threshold=12):
                messages.append(
                    f"{location} shows {match.group()!r}, which looks like a binary float repr"
                )
                break
    if not messages:
        return []
    return [
        ContentFinding(
            "content_float_noise", subject, messages[0].split(" ", 1)[0], _summarise(messages)
        )
    ]


# --------------------------------------------------------------------------------------------
# LaTeX and plain-text normalisation
# --------------------------------------------------------------------------------------------

_UNICODE_REPLACEMENTS = {
    "×": "*",
    "·": "*",
    "÷": "/",
    "−": "-",
    "–": "-",
    "—": "-",
    "≤": "<=",
    "⩽": "<=",
    "≥": ">=",
    "⩾": ">=",
    "≠": "!=",
    "≈": "≈",
    "π": "pi",
    "²": "^2",
    "³": "^3",
    "¹": "^1",
    "⁰": "^0",
    "⁴": "^4",
    "⁵": "^5",
    "½": "(1/2)",
    "⅓": "(1/3)",
    "⅔": "(2/3)",
    "¼": "(1/4)",
    "¾": "(3/4)",
    "⅕": "(1/5)",
    "⅛": "(1/8)",
    "°": "",
    "\u2009": " ",
    "\u202f": " ",
    "\u00a0": " ",
}
_SEPARATOR_COMMANDS = (
    "Longleftrightarrow",
    "Longrightarrow",
    "Leftrightarrow",
    "Rightarrow",
    "rightarrow",
    "therefore",
    "implies",
    "iff",
    "to",
)
_RELATION_COMMANDS = {
    "leqslant": "<=",
    "geqslant": ">=",
    "leq": "<=",
    "geq": ">=",
    "le": "<=",
    "ge": ">=",
    "neq": "!=",
    "ne": "!=",
    "lt": "<",
    "gt": ">",
    "approx": "≈",
}
_DROPPED_COMMANDS = {
    "left",
    "right",
    "displaystyle",
    "big",
    "Big",
    "bigg",
    "Bigg",
    "limits",
    "circ",
    "degree",
    "mathrm",
    "mathbf",
    "mathit",
    "operatorname",
}
_SPACING_COMMANDS = {",", ";", ":", "!", " ", "quad", "qquad", "enspace", "thinspace"}
_OPERATOR_COMMANDS = {"times": "*", "cdot": "*", "ast": "*", "div": "/", "pm": "±", "mp": "∓"}
_FUNCTION_COMMANDS = {"sin", "cos", "tan", "log", "ln", "sqrt"}
_TEXT_COMMANDS = {"text", "textrm", "textbf", "textit", "mbox", "mathrm", "operatorname"}


_DEGREE_MARK = re.compile(r"\^\s*(?:\{\s*\\circ\s*\}|\\circ\b|\{\s*\\degree\s*\})|\\degree\b")


def _read_group(text: str, index: int) -> tuple[str, int]:
    """Read a braced group, or a single token, starting at ``index``."""

    while index < len(text) and text[index] == " ":
        index += 1
    if index >= len(text):
        return "", index
    if text[index] == "{":
        depth = 0
        for end in range(index, len(text)):
            if text[end] == "{":
                depth += 1
            elif text[end] == "}":
                depth -= 1
                if depth == 0:
                    return text[index + 1 : end], end + 1
        return text[index + 1 :], len(text)
    if text[index] == "\\":
        match = re.match(r"\\[A-Za-z]+", text[index:])
        if match:
            return match.group(), index + len(match.group())
    return text[index], index + 1


def latex_to_plain(latex: str) -> str:
    """Convert a LaTeX fragment into the plain notation used by this module.

    Unknown commands are kept as ``\\name`` so that callers can refuse to evaluate them.
    Implication arrows become ``;`` segment separators, text groups are reduced to their
    words and braces become brackets.
    """

    latex = _DEGREE_MARK.sub("", latex)
    latex = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", latex)
    output: list[str] = []
    index = 0
    while index < len(latex):
        character = latex[index]
        if character == "\\":
            if latex.startswith("\\\\", index):
                output.append(" ; ")
                index += 2
                continue
            match = re.match(r"\\([A-Za-z]+|.)", latex[index:])
            name = match.group(1)
            index += len(match.group())
            if name in {"frac", "dfrac", "tfrac", "cfrac"}:
                numerator, index = _read_group(latex, index)
                denominator, index = _read_group(latex, index)
                output.append(f"(({latex_to_plain(numerator)})/({latex_to_plain(denominator)}))")
            elif name == "sqrt":
                degree = None
                if index < len(latex) and latex[index] == "[":
                    end = latex.find("]", index)
                    degree, index = latex[index + 1 : end], end + 1
                radicand, index = _read_group(latex, index)
                if degree:
                    output.append(f"root(({latex_to_plain(radicand)}),({latex_to_plain(degree)}))")
                else:
                    output.append(f"sqrt({latex_to_plain(radicand)})")
            elif name == "boxed":
                content, index = _read_group(latex, index)
                output.append(f" {latex_to_plain(content)} ")
            elif name in _TEXT_COMMANDS:
                content, index = _read_group(latex, index)
                output.append(f" \u27e8{content}\u27e9 ")
            elif name in _SEPARATOR_COMMANDS:
                output.append(" ; ")
            elif name in _RELATION_COMMANDS:
                output.append(f" {_RELATION_COMMANDS[name]} ")
            elif name in _OPERATOR_COMMANDS:
                output.append(f" {_OPERATOR_COMMANDS[name]} ")
            elif name in _SPACING_COMMANDS:
                output.append(" ")
            elif name in _DROPPED_COMMANDS:
                continue
            elif name == "pi":
                output.append(" pi ")
            elif name == "%":
                output.append("%")
            elif name in {"{", "}"}:
                output.append(name)
            elif name in _FUNCTION_COMMANDS:
                output.append(f" {name} ")
            else:
                output.append(f"\\{name}")
            continue
        if character == "{":
            if latex.startswith("{,}", index):
                index += 3
                continue
            output.append("(")
        elif character == "}":
            output.append(")")
        elif character == "&":
            output.append(" ")
        else:
            output.append(character)
        index += 1
    plain = "".join(output)
    # Degree markers such as ^\circ or ^(\circ) disappear with \circ itself.
    plain = re.sub(r"\^\s*\(\s*\)", "", plain)
    plain = re.sub(r"\^(?=\s*(?:[;,=<>)]|$))", "", plain)
    return plain


def plain_text_to_plain(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    for source, target in _UNICODE_REPLACEMENTS.items():
        text = text.replace(source, target)
    text = re.sub(r"√\s*\(", "sqrt(", text)
    text = re.sub(r"√\s*(\d+(?:\.\d+)?|[A-Za-z])", r"sqrt(\1)", text)
    return text


def to_plain(block_type: str, value: str) -> str:
    if block_type == "text":
        return plain_text_to_plain(value)
    return plain_text_to_plain(latex_to_plain(value))


# --------------------------------------------------------------------------------------------
# Safe arithmetic evaluation
# --------------------------------------------------------------------------------------------

Number = Fraction | float


class _EvaluationError(ValueError):
    pass


_TOKEN = re.compile(
    r"\s*(?:(?P<number>\d+(?:\.\d+)?|\.\d+)|(?P<name>sqrt|root|sin|cos|tan|pi|[A-Za-z](?:_\w)?)"
    r"|(?P<op>\*\*|[-+*/^(),]))"
)


def _tokens(expression: str) -> list[tuple[str, str]]:
    expression = re.sub(r"(?<=\d) (?=\d{3}(?!\d))", "", expression.strip())
    tokens: list[tuple[str, str]] = []
    index = 0
    while index < len(expression):
        match = _TOKEN.match(expression, index)
        if match is None or match.end() == index:
            if expression[index:].strip() == "":
                break
            raise _EvaluationError(f"Unsupported token at {expression[index:index + 10]!r}")
        kind = match.lastgroup
        tokens.append((kind, match.group(kind)))
        index = match.end()
    # Insert implicit multiplication: 2x, 2(…), )(, x(, )2, x y.
    result: list[tuple[str, str]] = []
    for token in tokens:
        if result:
            previous_kind, previous = result[-1]
            ends_value = previous_kind in {"number", "name"} or previous == ")"
            starts_value = token[0] in {"number", "name"} or token[1] == "("
            if (
                ends_value
                and starts_value
                and previous not in {"sqrt", "root", "sin", "cos", "tan"}
            ):
                result.append(("op", "*"))
        result.append(token)
    return result


class _Parser:
    def __init__(self, tokens, variables: dict[str, Number]):
        self.tokens = tokens
        self.index = 0
        self.variables = variables

    def peek(self):
        return self.tokens[self.index] if self.index < len(self.tokens) else (None, None)

    def take(self, value=None):
        token = self.peek()
        if token == (None, None) or (value is not None and token[1] != value):
            raise _EvaluationError(f"Expected {value}")
        self.index += 1
        return token

    def parse(self) -> Number:
        value = self.expression()
        if self.index != len(self.tokens):
            raise _EvaluationError("Trailing tokens")
        return value

    def expression(self) -> Number:
        value = self.term()
        while self.peek()[1] in {"+", "-"}:
            operator = self.take()[1]
            right = self.term()
            value = value + right if operator == "+" else value - right
        return value

    def term(self) -> Number:
        value = self.unary()
        while self.peek()[1] in {"*", "/"}:
            operator = self.take()[1]
            right = self.unary()
            if operator == "*":
                value = value * right
            else:
                if right == 0:
                    raise _EvaluationError("Division by zero")
                value = value / right
        return value

    def unary(self) -> Number:
        if self.peek()[1] == "-":
            self.take()
            return -self.unary()
        if self.peek()[1] == "+":
            self.take()
            return self.unary()
        return self.power()

    def power(self) -> Number:
        base = self.atom()
        if self.peek()[1] in {"^", "**"}:
            self.take()
            exponent = self.unary()
            return _power(base, exponent)
        return base

    def atom(self) -> Number:
        kind, value = self.peek()
        if kind == "number":
            self.take()
            return Fraction(value)
        if kind == "name":
            self.take()
            if value == "pi":
                return math.pi
            if value in {"sqrt", "sin", "cos", "tan"}:
                argument = self.function_argument()
                if value == "sqrt":
                    if argument < 0:
                        raise _EvaluationError("Negative square root")
                    return _exact_root(argument, 2)
                radians = math.radians(float(argument))
                return {"sin": math.sin, "cos": math.cos, "tan": math.tan}[value](radians)
            if value == "root":
                self.take("(")
                radicand = self.expression()
                self.take(",")
                degree = self.expression()
                self.take(")")
                return _exact_root(radicand, int(degree))
            if value not in self.variables:
                raise _EvaluationError(f"Unknown variable {value}")
            return self.variables[value]
        if value == "(":
            self.take()
            inner = self.expression()
            self.take(")")
            return inner
        raise _EvaluationError(f"Unexpected token {value}")

    def function_argument(self) -> Number:
        if self.peek()[1] == "(":
            self.take()
            inner = self.expression()
            self.take(")")
            return inner
        return self.power()


def _exact_root(value: Number, degree: int) -> Number:
    if isinstance(value, Fraction) and value >= 0:
        numerator = round(value.numerator ** (1 / degree))
        denominator = round(value.denominator ** (1 / degree))
        if numerator**degree == value.numerator and denominator**degree == value.denominator:
            return Fraction(numerator, denominator)
    if value < 0 and degree % 2 == 1:
        return -(float(-value) ** (1 / degree))
    return float(value) ** (1 / degree)


def _power(base: Number, exponent: Number) -> Number:
    if isinstance(exponent, Fraction) and exponent.denominator == 1:
        if abs(exponent) > 64:
            raise _EvaluationError("Exponent too large")
        if base == 0 and exponent < 0:
            raise _EvaluationError("Division by zero")
        return base ** int(exponent)
    if base < 0:
        raise _EvaluationError("Fractional power of a negative number")
    return float(base) ** float(exponent)


def evaluate(expression: str, variables: dict[str, Number] | None = None) -> Number:
    """Evaluate a plain expression; raise ``ValueError`` when it is not purely arithmetic."""

    cleaned = expression.replace("\u27e8", " ").replace("\u27e9", " ")
    if "\\" in cleaned or "\u27e8" in expression:
        raise _EvaluationError("Unsupported LaTeX or text")
    if not re.search(r"\d|pi", cleaned):
        raise _EvaluationError("No number")
    return _Parser(_tokens(cleaned), variables or {}).parse()


def try_evaluate(expression: str, variables: dict[str, Number] | None = None) -> Number | None:
    try:
        value = evaluate(expression, variables)
    except (ValueError, ZeroDivisionError, OverflowError, TypeError):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, complex):
        return None
    return value


_STRIP_UNIT = re.compile(
    r"\u27e8[^\u27e9]*\u27e9|\b(?:cm|mm|km|m|kg|g|ml|l|s|h|min|units?)\b(?:\s*\^\s*[23])?"
)


def parse_value(text: str) -> Number | None:
    """Parse a final-result string such as '84 cm', '\\frac{7}{12}', '100\\%' or '15.0'."""

    plain = to_plain("latex", text) if "\\" in text else plain_text_to_plain(text)
    plain = _STRIP_UNIT.sub(" ", plain)
    plain = plain.replace("%", " ").replace("$", " ")
    plain = re.sub(r"\(\s*\d+\s*(?:d\.p\.|s\.f\.|dp|sf)\s*\)", " ", plain)
    plain = plain.strip().rstrip(".").strip()
    if not plain or re.search(r"[A-Za-z]", plain.replace("pi", "").replace("sqrt", "")):
        return None
    return try_evaluate(plain)


def _close(left: Number, right: Number, *, relative: float = 1e-9) -> bool:
    if isinstance(left, Fraction) and isinstance(right, Fraction):
        return left == right
    return math.isclose(float(left), float(right), rel_tol=relative, abs_tol=1e-9)


def _decimal_places(literal: str) -> int | None:
    match = re.fullmatch(r"\s*-?\d+(?:\.(\d+))?\s*", literal)
    if match is None:
        return None
    return len(match.group(1) or "")


def _consistent_with_rounding(exact: Number, shown: Number, literal: str) -> bool:
    """Whether ``shown`` (written as ``literal``) is ``exact`` or a rounding of it."""

    if _close(exact, shown):
        return True
    places = _decimal_places(literal)
    exact_float, shown_float = float(exact), float(shown)
    if places is not None:
        if abs(exact_float - shown_float) <= 0.5 * 10 ** (-places) + 1e-9:
            return True
        # Integers written as rounded significant figures (48 400 for 48 372).
        digits = len(re.sub(r"\D", "", literal.split(".")[0]).lstrip("0")) or 1
        if places == 0 and abs(shown_float) >= 10:
            for significant in range(1, digits + 1):
                magnitude = 10 ** (math.floor(math.log10(abs(exact_float or 1))) - significant + 1)
                if abs(round(exact_float / magnitude) * magnitude - shown_float) < 1e-6:
                    return True
    return False


# --------------------------------------------------------------------------------------------
# Check: plain-text maths in text blocks
# --------------------------------------------------------------------------------------------

_PLAIN_MATH_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("raw LaTeX command", re.compile(r"\\(?:[A-Za-z]{2,}|[,;!])")),
    ("function-call root", re.compile(r"\b(?:sqrt|cbrt|root)\s*\(", re.I)),
    ("caret exponent", re.compile(r"[\w)\]]\s*\^\s*[-+\w(]")),
    ("ASCII relation", re.compile(r"(?<![<>=!-])(?:<=|>=|!=|=<|=>|<>)(?![<>=])")),
    ("asterisk multiplication", re.compile(r"[\w)]\s*\*\s*[\w(]")),
    (
        "bracketed slash fraction",
        re.compile(r"\)\s*/\s*[\w(]|(?<![\w/])[\w.]+\s*/\s*\((?![a-z]{2,}\b)"),
    ),
]


def plain_text_math_findings(
    text_blocks: Iterable[tuple[str, str]], subject: str
) -> list[ContentFinding]:
    messages: list[str] = []
    first_location = ""
    for location, text in text_blocks:
        for label, pattern in _PLAIN_MATH_PATTERNS:
            match = pattern.search(text)
            if match is None:
                continue
            excerpt = text[max(0, match.start() - 20) : match.end() + 20].strip()
            messages.append(f"{location}: {label} in {excerpt!r}")
            first_location = first_location or location
            break
    if not messages:
        return []
    return [
        ContentFinding(
            "content_plain_text_math",
            subject,
            first_location,
            _summarise(messages) + " (use inline_math or display_math blocks)",
        )
    ]


# --------------------------------------------------------------------------------------------
# Check: prompt with no question
# --------------------------------------------------------------------------------------------

_INSTRUCTION_VERBS = (
    r"find|calculate|work\s+out|write|express|give|enter|determine|solve|simplify|expand|"
    r"factori[sz]e|evaluate|state|show|estimate|convert|round|list|name|identify|choose|"
    r"select|order|arrange|complete|make|compare|decide|explain|classify|prove|construct|"
    r"draw|measure|increase|decrease|divide|share|use|insert|type|record|count|compute|"
    r"obtain|deduce|test|check|verify|justify|rewrite|reduce|substitute|plot|sketch|read|"
    r"describe|predict|apply|form|translate|rearrange|rank|sort|match|shade|mark|label|fill|"
    r"correct|multiply|add|subtract|recall|isolate|undo|clear|remove|collect|treat|move|"
    r"eliminate|distribute|reflect|rotate|enlarge|copy|bisect|answer|respond|recover|"
    r"interpret|suggest|exchange|split|change|tell"
)
_INSTRUCTION = re.compile(
    r"\?|(?:^|[.:;!,|—–]\s*|\b(?:then|and|to|please|now)\s+)(?:"
    + _INSTRUCTION_VERBS
    + r")\b|\b(?:how\s+many|how\s+much|how\s+long|how\s+far|how\s+old|what|which|who|"
    r"when|where|whether)\b",
    re.IGNORECASE,
)


def has_instruction(blocks_texts: Iterable[str]) -> bool:
    return _INSTRUCTION.search(" | ".join(blocks_texts)) is not None


def prompt_without_question_findings(
    prompts: Iterable[tuple[str, list[str]]], subject: str
) -> list[ContentFinding]:
    findings = []
    for location, texts in prompts:
        if has_instruction(texts):
            continue
        visible = " ".join(text.strip() for text in texts if text.strip())
        findings.append(
            ContentFinding(
                "content_prompt_without_question",
                subject,
                location,
                f"The learner-visible prompt states no question or instruction: {visible[:160]!r}",
            )
        )
    return findings


# --------------------------------------------------------------------------------------------
# Number extraction shared by the hint, mismatch and duplicate checks
# --------------------------------------------------------------------------------------------

_NUMBER_IN_PLAIN = re.compile(
    r"(?<![\w.^])(-?\d+(?:\.\d+)?)(?:\s*\)?\s*/\s*\(?\s*(\d+(?:\.\d+)?)(?![\w(.]))?(?![\w.]*\d)"
)


def _numbers(plain: str) -> list[tuple[Fraction, int, int, str]]:
    plain = re.sub(r"(?<=\d) (?=\d{3}(?!\d))", "", plain)
    results = []
    for match in _NUMBER_IN_PLAIN.finditer(plain):
        try:
            value = Fraction(match.group(1))
            if match.group(2):
                value /= Fraction(match.group(2))
        except (ValueError, ZeroDivisionError):
            continue
        results.append((value, match.start(), match.end(), match.group()))
    return results


def _block_plain(block) -> str:
    return to_plain(block.type, _block_text(block))


# --------------------------------------------------------------------------------------------
# Check: hints that reveal the answer
# --------------------------------------------------------------------------------------------

_RESULT_CONTEXT = re.compile(
    r"(?:=|≈|\bis|\bare|\bequals?|\bgives?|\bget|\bgets|\bmakes?|\bbecomes?|\bleaves?|"
    r"\banswer)\s*\(?\s*$",
    re.IGNORECASE,
)
_ASSIGNED_VARIABLE = re.compile(r"(?<![A-Za-z])([A-Za-z])(?:_\w)?\s*=\s*\(?\s*$")
_ASKED_VARIABLE = re.compile(
    r"\b(?:find|calculate|determine|work\s+out|state|give|enter)\s+(?:the\s+value\s+of\s+|"
    r"the\s+values?\s+of\s+)?([A-Za-z])\b(?!\s*[A-Za-z])",
    re.IGNORECASE,
)


def _asked_variables(prompt_plain: str) -> set[str]:
    variables = set()
    for match in _ASKED_VARIABLE.finditer(prompt_plain):
        letter = match.group(1)
        if letter.lower() == "a" and re.search(r"\b[Aa]\s+[a-z]{2,}", prompt_plain[match.start(1) :]):
            continue
        variables.add(letter)
    return variables


def _normalised_expression(value: str) -> str:
    plain = to_plain("latex", value)
    plain = plain.replace("**", "^").replace("*", "")
    return re.sub(r"\s+", "", plain).replace("(", "").replace(")", "")


def hint_answer_findings(question: Question) -> list[ContentFinding]:
    findings = []
    stem_plain = " ".join(_block_plain(block) for block in question.stem)
    for part_index, part in enumerate(question.parts):
        response = part.response
        prompt_plain = stem_plain + " " + " ".join(_block_plain(block) for block in part.prompt)
        asked = _asked_variables(prompt_plain)
        for hint_index, hint in enumerate(part.hints):
            location = f"parts[{part_index}].hints[{hint_index}]"
            hint_plain = " ".join(_block_plain(block) for block in hint.content)
            reason = None
            if isinstance(response, NumericResponse):
                reason = _numeric_hint_leak(response, hint_plain, asked, prompt_plain)
            elif (
                isinstance(response, AlgebraicResponse)
                and response.comparison_mode == "symbolic_equivalence"
            ):
                expression = _normalised_expression(response.canonical_expression)
                if len(expression) >= 5 and re.search(r"[A-Za-z]", expression):
                    hint_expression = _normalised_expression(
                        " ".join(_block_text(block) for block in hint.content)
                    )
                    if expression in hint_expression:
                        reason = (
                            f"contains the canonical expression "
                            f"{response.canonical_expression!r}"
                        )
            if reason:
                findings.append(
                    ContentFinding(
                        "content_hint_reveals_answer",
                        question.stable_key,
                        location,
                        f"Stage-{hint.stage} hint {reason}: "
                        f"{' '.join(_block_text(block) for block in hint.content)[:160]!r}",
                    )
                )
    return findings


def _numeric_hint_leak(
    response: NumericResponse, hint_plain: str, asked: set[str], prompt_plain: str
) -> str | None:
    answer = parse_value(response.canonical_answer)
    asks_percentage = re.search(
        r"percentage|as\s+a\s+per\s*cent|what\s+per\s*cent", prompt_plain, re.IGNORECASE
    )
    if answer is None or not isinstance(answer, Fraction) or answer in {0, 1, -1}:
        return None
    for value, start, end, literal in _numbers(hint_plain):
        if value != answer:
            continue
        before = hint_plain[:start]
        following = hint_plain[end:].lstrip()
        operand = re.match(
            r"(?:[-+*/^]|times\b|plus\b|minus\b|multipl|divided\b|of\b|over\b)",
            following,
            re.IGNORECASE,
        ) or re.search(r"(?:[-+*/^]|times|plus|minus|of)\s*$", before, re.IGNORECASE)
        if "/" in literal and answer.denominator != 1 and not operand:
            numerator, denominator = (Fraction(item) for item in literal.split("/"))
            if Fraction(numerator) / Fraction(denominator) == answer and (
                numerator,
                denominator,
            ) != (answer.numerator, answer.denominator):
                return f"states the answer as the unsimplified fraction {literal.strip()}"
            return f"states the exact answer {literal.strip()}"
        if _RESULT_CONTEXT.search(before):
            assigned = _ASSIGNED_VARIABLE.search(before)
            if assigned and asked and assigned.group(1) not in asked:
                continue
            if assigned and re.search(r"substitut|replace|use\s+the\s+point", before, re.I):
                continue
            if following.startswith("%") and not asks_percentage:
                continue
            if following[:1] in {"*", "/", "^", "+", "-"} or re.match(r"[A-Za-z(]", following[:1]):
                if not re.match(r"(?:cm|mm|km|m|kg|g|units?|degrees?|°|%|and|or|so|,)", following):
                    continue
            return f"states the answer {literal.strip()} as a result"
    return None


# --------------------------------------------------------------------------------------------
# Check: canonical answer against the worked solution
# --------------------------------------------------------------------------------------------

_TEXT_GROUP = re.compile(r"\u27e8[^\u27e9]*\u27e9")
_LONE_VALUE = re.compile(
    r"\s*-?\s*(?:\d+(?:\.\d+)?|\(\(\s*-?\d+(?:\.\d+)?\s*\)/\(\s*\d+(?:\.\d+)?\s*\)\)|"
    r"\d+\s*/\s*\d+)(?:\s*\*?\s*pi)?\s*%?\s*\.?\s*"
)
_DECISION_PROMPT = re.compile(
    r"\benter\s+[01]\s+if\b|\bcodes?\b|\buse\s+\d\s+(?:for|if)\b", re.IGNORECASE
)


def _segments(plain: str) -> list[str]:
    """Split a plain math string into independent statements."""

    plain = re.sub(
        r"\u27e8\s*(?:or|and|so|hence|thus|since|because|when|if|then|giving|gives|check:?)"
        r"\s*[,:]?\s*\u27e9",
        ";",
        plain,
        flags=re.IGNORECASE,
    )
    parts = re.split(r";|,(?![^()]*\))|\s{3,}", plain)
    return [part.strip() for part in parts if part.strip()]


def _relation_chain(segment: str) -> tuple[list[str], list[str]] | None:
    pieces = re.split(r"(<=|>=|!=|≈|=|<|>)", segment)
    if len(pieces) < 3:
        return None
    sides = [piece.strip() for piece in pieces[0::2]]
    relations = pieces[1::2]
    if any(not side for side in sides):
        return None
    return sides, relations


def _side_value(side: str) -> tuple[Number | None, str, str]:
    """Evaluate one side of a relation: (value, numeric literal, trailing unit text)."""

    side = side.strip()
    if side.startswith("\u27e8"):
        return None, "", ""
    unit = ""
    match = _TEXT_GROUP.search(side)
    if match:
        unit = re.sub(r"\s+", " ", side[match.start() :].replace("\u27e8", "").replace("\u27e9", ""))
        side = side[: match.start()].strip()
    literal = side.rstrip("%").strip()
    value = try_evaluate(literal)
    if value is not None and side.endswith("%"):
        value = value / 100
    return value, literal, unit.strip()


def _final_result(part) -> tuple[str, str] | None:
    """Return (literal, location) for the single value the worked solution ends with."""

    last_index = len(part.solution) - 1
    location = f"solution[{last_index}]"
    last = part.solution[-1]
    candidate = None
    for block in last.content:
        if block.type in {"inline_math", "display_math"} and "\\boxed" in block.latex:
            content, _ = _read_group(block.latex, block.latex.index("\\boxed") + 6)
            plain = to_plain("latex", content)
            candidate = re.split(r"=|≈", plain)[-1]
            break
    if candidate is None:
        for block in reversed(last.content):
            if block.type == "asset_ref":
                continue
            plain = to_plain(block.type, _block_text(block))
            if block.type == "text":
                match = re.search(
                    r"(?:=|≈|\bis|\bequals|\bgives|\banswer:?|->)\s*\$?\s*"
                    r"(-?\d[\d ,]*(?:\.\d+)?(?:\s*/\s*\d+)?)\s*(?:%|[a-zA-Z]+(?:\^[23])?)?"
                    r"\s*\.?\s*$",
                    plain,
                )
                if match:
                    candidate = match.group(1).replace(",", "")
                elif _LONE_VALUE.fullmatch(plain):
                    candidate = plain
                break
            segments = _segments(plain)
            if not segments:
                break
            chain = _relation_chain(segments[-1])
            if chain is None:
                candidate = segments[-1]
            elif chain[1][-1] in {"=", "≈"}:
                candidate = chain[0][-1]
            break
    if candidate is None:
        return None
    candidate = _TEXT_GROUP.split(candidate)[0].strip()
    if not _LONE_VALUE.fullmatch(candidate):
        return None
    return candidate.strip().rstrip("."), location


def _solution_results(part) -> list[Number]:
    """Every value the solution states as a result (right of '=' or '≈', or boxed)."""

    values: list[Number] = []
    for step in part.solution:
        for block in step.content:
            if block.type == "asset_ref":
                continue
            plain = to_plain(block.type, _block_text(block))
            for segment in _segments(plain):
                chain = _relation_chain(segment)
                if chain is None:
                    value = try_evaluate(_TEXT_GROUP.split(segment)[0].rstrip("%. ").strip())
                    if value is not None:
                        values.append(value)
                    continue
                for side in chain[0][1:]:
                    value, _, _ = _side_value(side)
                    if value is not None:
                        values.append(value)
                    for number, *_ in _numbers(_TEXT_GROUP.sub(" ", side)):
                        values.append(number)
            if block.type == "text":
                for number, *_ in _numbers(plain):
                    values.append(number)
    return values


def _answer_matches(response: NumericResponse, solution_value: Number, literal: str) -> bool:
    answer = parse_value(response.canonical_answer)
    if answer is None:
        return True
    candidates = [solution_value]
    if "pi" in literal:
        coefficient = parse_value(literal.replace("pi", "").replace("*", " "))
        if coefficient is not None:
            candidates.append(coefficient)
    accepted = [
        value for value in (parse_value(item) for item in response.accepted_answers) if value
    ]
    for candidate in candidates:
        if _close(answer, candidate) or any(_close(item, candidate) for item in accepted):
            return True
        if response.comparison_mode in {"rounded_dp", "rounded_sf"}:
            if _consistent_with_rounding(candidate, answer, response.canonical_answer):
                return True
        elif response.comparison_mode == "absolute_tolerance" and response.absolute_tolerance:
            tolerance = float(Fraction(response.absolute_tolerance))
            if abs(float(answer) - float(candidate)) <= tolerance + 1e-9:
                return True
        elif _consistent_with_rounding(answer, candidate, literal) and _decimal_places(
            literal
        ) not in {None, 0}:
            return True
    return False


def _numeric_chain_errors(plain: str) -> list[str]:
    """Return false purely-numerical equalities such as '55^2+72^2=8209'."""

    errors = []
    for segment in _segments(plain):
        if "..." in segment or "\u2026" in segment:
            continue
        chain = _relation_chain(segment)
        if chain is None:
            continue
        sides, relations = chain
        evaluated = [_side_value(side) for side in sides]
        for index, relation in enumerate(relations):
            left, _, left_unit = evaluated[index]
            right, literal, right_unit = evaluated[index + 1]
            if relation != "=" or left is None or right is None:
                continue
            if left_unit != right_unit:
                continue
            if _consistent_with_rounding(left, right, literal):
                continue
            # Allow '=' written for a rounded intermediate value (about 1 % error).
            if not isinstance(left, Fraction) or not isinstance(right, Fraction):
                if math.isclose(float(left), float(right), rel_tol=0.01):
                    continue
            errors.append(f"{sides[index]} = {sides[index + 1]} is false ({_fmt(left)})")
    return errors


def _fmt(value: Number) -> str:
    if isinstance(value, Fraction):
        if value.denominator == 1:
            return str(value.numerator)
        return f"{value.numerator}/{value.denominator} ≈ {float(value):.6g}"
    return f"{value:.6g}"


def _single_variable_equations(plain: str) -> list[tuple[str, str, str]]:
    equations = []
    for segment in _segments(plain):
        chain = _relation_chain(segment)
        if chain is None:
            continue
        sides, relations = chain
        if len(sides) != 2 or relations != ["="]:
            continue
        names = set(re.findall(r"(?<![A-Za-z\\])([A-Za-z])(?![A-Za-z])", segment))
        names -= {"pi"}
        if len(names) == 1:
            equations.append((sides[0], sides[1], names.pop()))
    return equations


def _assignment(plain: str) -> tuple[str, Number, str] | None:
    segments = _segments(plain)
    if not segments:
        return None
    match = re.fullmatch(
        r"([A-Za-z])\s*=\s*(-?[\d.]+(?:\s*/\s*\d+)?|\(\(-?\d+\)/\(\d+\)\))", segments[-1].strip()
    )
    if match is None:
        return None
    value = try_evaluate(match.group(2))
    if value is None:
        return None
    return match.group(1), value, match.group(2)


_BINARY_DECISION = re.compile(r"\benter\s+1\s+if\b.*\b0\s+if\b", re.IGNORECASE | re.DOTALL)


def _binary_decision_error(question: Question, part, response: NumericResponse) -> str | None:
    prompt = _blocks_text(question.stem) + " " + _blocks_text(part.prompt)
    if not _BINARY_DECISION.search(prompt) or response.canonical_answer not in {"0", "1"}:
        return None
    if not re.search(r"right[- ]angled|equal|same", prompt, re.IGNORECASE):
        return None
    for step in part.solution:
        for block in step.content:
            if block.type not in {"inline_math", "display_math"}:
                continue
            statements = [
                _relation_chain(segment) for segment in _segments(to_plain(block.type, block.latex))
            ]
            statements = [item for item in statements if item and item[1][-1] == "="]
            if len(statements) != 2:
                continue
            compared = [try_evaluate(sides[-1]) for sides, _ in statements]
            if any(value is None for value in compared):
                continue
            equal = _close(compared[0], compared[1])
            expected = "1" if equal else "0"
            if expected != response.canonical_answer:
                return (
                    f"the solution compares {_fmt(compared[0])} with {_fmt(compared[1])} "
                    f"({'equal' if equal else 'not equal'}), so the answer should be {expected}, "
                    f"but the canonical answer is {response.canonical_answer}"
                )
    return None


def answer_solution_findings(question: Question) -> list[ContentFinding]:
    findings = []
    for part_index, part in enumerate(question.parts):
        response = part.response
        if not isinstance(response, NumericResponse):
            continue
        messages = []
        prompt_text = _blocks_text(question.stem) + " " + _blocks_text(part.prompt)
        final = None if _DECISION_PROMPT.search(prompt_text) else _final_result(part)
        if final is not None:
            literal, location = final
            value = parse_value(literal)
            answer = parse_value(response.canonical_answer)
            stated = _solution_results(part)
            if (
                value is not None
                and answer is not None
                and not _answer_matches(response, value, literal)
                and not any(_answer_matches(response, item, str(item)) for item in stated)
            ):
                messages.append(
                    f"{location} ends with {literal.strip()!r} but the canonical answer is "
                    f"{response.canonical_answer!r}"
                )
        decision = _binary_decision_error(question, part, response)
        if decision:
            messages.append(decision)
        assignment = None
        for step in reversed(part.solution):
            for block in reversed(step.content):
                if block.type in {"inline_math", "display_math"}:
                    assignment = _assignment(to_plain(block.type, block.latex))
                    if assignment:
                        break
            if assignment:
                break
        for step_index, step in enumerate(part.solution):
            for block in step.content:
                if block.type not in {"inline_math", "display_math"}:
                    continue
                plain = to_plain(block.type, block.latex)
                for error in _numeric_chain_errors(plain):
                    messages.append(f"solution[{step_index}]: {error}")
                if assignment is None:
                    continue
                name, value, literal = assignment
                for left, right, variable in _single_variable_equations(plain):
                    if variable != name:
                        continue
                    left_value = try_evaluate(left, {name: value})
                    right_value = try_evaluate(right, {name: value})
                    if left_value is None or right_value is None:
                        continue
                    if _close(left_value, right_value, relative=1e-6):
                        continue
                    if not isinstance(value, Fraction) or _decimal_places(literal):
                        if math.isclose(float(left_value), float(right_value), rel_tol=0.01):
                            continue
                    messages.append(
                        f"solution[{step_index}]: {name} = {literal} does not satisfy "
                        f"{left} = {right} ({_fmt(left_value)} vs {_fmt(right_value)})"
                    )
        if messages:
            unique = list(dict.fromkeys(messages))
            findings.append(
                ContentFinding(
                    "content_answer_solution_mismatch",
                    question.stable_key,
                    f"parts[{part_index}]",
                    _summarise(unique),
                )
            )
    return findings


# --------------------------------------------------------------------------------------------
# Check: math-identical items
# --------------------------------------------------------------------------------------------

_CONCEPT_WORDS = (
    "mean",
    "median",
    "mode",
    "range",
    "area",
    "perimeter",
    "volume",
    "surface",
    "circumference",
    "radius",
    "diameter",
    "height",
    "length",
    "width",
    "angle",
    "gradient",
    "intercept",
    "hcf",
    "lcm",
    "highest common factor",
    "lowest common multiple",
    "factor",
    "multiple",
    "prime",
    "probability",
    "percentage",
    "percent",
    "ratio",
    "speed",
    "distance",
    "time",
    "interest",
    "discount",
    "profit",
    "loss",
    "expand",
    "factorise",
    "simplify",
    "solve",
    "subject",
    "sum",
    "difference",
    "product",
    "quotient",
    "increase",
    "decrease",
    "frequency",
    "total",
    "larger",
    "smaller",
    "greatest",
    "least",
    "interior",
    "exterior",
    "hypotenuse",
    "scale",
    "coordinate",
)
_CONCEPT = re.compile(r"\b(" + "|".join(_CONCEPT_WORDS) + r")s?\b", re.IGNORECASE)
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])|\n+")
_UNIT_AFTER_NUMBER = re.compile(
    r"(?<=\d)\s*(?:mm|cm|km|m|kg|g|ml|l|s|h|min|hr)\b(?:\s*\^\s*[23])?"
)
_CODE_SENTENCE = re.compile(
    r"\bcodes?\b|\benter\s+[01]\s+if\b|\b0\s+if\b|\benter\s+1\s+or\s+0\b", re.IGNORECASE
)
_LABEL_PREFIX = re.compile(r"^[^.?!]{0,160}(?:\u2014|:)\s+")
_STOP_WORDS = frozenset(
    "about after also answer before code codes each enter from have into most only suitable "
    "that their them then there these they this those what when where which while with would "
    "your number value values given using used".split()
)


@dataclass(frozen=True)
class MathSignature:
    numbers: tuple[Fraction, ...]
    ordered_numbers: tuple[Fraction, ...]
    skeleton: str
    variables: tuple[str, ...]
    operators: tuple[str, ...]
    concepts: tuple[str, ...]
    words: tuple[str, ...]
    answer: str | None

    @property
    def strength(self) -> int:
        return len(self.numbers) + len(self.variables) + (2 if self.words else 0)


def _prompt_plain(blocks) -> str:
    combined = []
    for block in blocks:
        if block.type == "asset_ref":
            continue
        if block.type == "text":
            combined.append(plain_text_to_plain(block.text))
        else:
            combined.append(" " + to_plain(block.type, block.latex) + " ")
    return "".join(combined)


def _is_math_sentence(sentence: str) -> bool:
    return re.search(
        r"\d|(?<![A-Za-z])[a-z](?![A-Za-z])\s*[=+*/^<>-]|[=+*/^<>]", sentence
    ) is not None


def _answer_key(response) -> str | None:
    if response is None:
        return None
    if isinstance(response, NumericResponse):
        value = parse_value(response.canonical_answer)
        return f"n:{value}" if value is not None else f"s:{response.canonical_answer.strip()}"
    expression = _normalised_expression(response.canonical_expression)
    return f"e:{expression}"


def math_signature(blocks, response=None) -> MathSignature:
    """Reduce a prompt to its mathematical core.

    Sentences without numbers, variables or operators are context and are dropped.  LaTeX and
    plain text are first converted to one notation, so '\\frac{3}{4}' and '3/4' agree.  For
    code-selection prompts, whose task is described in words, the remaining scenario words
    form the signature instead.
    """

    text = _prompt_plain(blocks)
    all_sentences = [item for item in _SENTENCE_SPLIT.split(text) if item.strip()]
    code_prompt = any(_CODE_SENTENCE.search(sentence) for sentence in all_sentences)
    sentences = [
        sentence
        for sentence in all_sentences
        if not (code_prompt and _CODE_SENTENCE.search(sentence))
    ]
    numbers: list[Fraction] = []
    skeleton: list[str] = []
    variables: set[str] = set()
    operators: set[str] = set()
    concepts = {
        match.lower()
        for sentence in all_sentences
        for match in _CONCEPT.findall(_LABEL_PREFIX.sub("", sentence))
    }
    for sentence in sentences:
        if not _is_math_sentence(sentence):
            continue
        stripped = _UNIT_AFTER_NUMBER.sub(" ", _TEXT_GROUP.sub(" ", sentence))
        for value, *_ in _numbers(stripped):
            numbers.append(abs(value))
        skeleton.extend(re.findall(r"[-+*/^=<>]", stripped))
        for name in re.findall(r"(?<![A-Za-z\\])([a-z])(?![A-Za-z])", stripped):
            if name != "a" or re.search(r"\ba\s*[=+*/^-]|[=+*/^-]\s*a\b", stripped):
                variables.add(name)
        operators.update(re.findall(r"sqrt|\^|[<>]=?|!=", stripped))
    words: tuple[str, ...] = ()
    if code_prompt and len(numbers) < 2:
        scenario = " ".join(_LABEL_PREFIX.sub("", sentence) for sentence in all_sentences)
        words = tuple(
            sorted(
                {
                    word
                    for word in re.findall(r"[a-z]{4,}", scenario.casefold())
                    if word not in _STOP_WORDS
                }
            )
        )
    return MathSignature(
        tuple(sorted(numbers)),
        tuple(numbers),
        "".join(skeleton),
        tuple(sorted(variables)),
        tuple(sorted(operators)),
        tuple(sorted(concepts)),
        words,
        _answer_key(response),
    )


@dataclass(frozen=True)
class MathItem:
    subject: str
    location: str
    group: str
    topic: str
    signature: MathSignature
    kind: Literal["question", "lesson"]


def question_math_items(question: Question) -> list[MathItem]:
    items = []
    for part_index, part in enumerate(question.parts):
        blocks = [*(question.stem if part_index == 0 else []), *part.prompt]
        items.append(
            MathItem(
                question.stable_key,
                f"parts[{part_index}]",
                question.bank_key,
                question.topic_code.lower(),
                math_signature(blocks, part.response),
                "question",
            )
        )
    return items


def lesson_math_items(lesson) -> list[MathItem]:
    items = []
    for index, section in enumerate(lesson.sections):
        if section.type == "worked_example":
            signature = math_signature(section.prompt)
        elif section.type == "active_recall":
            signature = math_signature(section.prompt, section.response)
        else:
            continue
        items.append(
            MathItem(
                lesson.stable_key,
                f"sections[{index}] {section.stable_key}",
                lesson.course_key,
                lesson.stable_key.split("-", 1)[0],
                signature,
                "lesson",
            )
        )
    return items


def _concepts_compatible(first: MathSignature, second: MathSignature) -> bool:
    if not first.concepts or not second.concepts:
        return True
    return bool(set(first.concepts) & set(second.concepts))


def _strict_key(signature: MathSignature):
    return (
        signature.numbers,
        signature.variables,
        signature.operators,
        signature.words,
        signature.answer,
    )


def _loose_key(signature: MathSignature):
    return (
        signature.ordered_numbers,
        signature.skeleton,
        signature.variables,
        signature.operators,
        signature.words,
    )


def math_duplicate_findings(
    items: list[MathItem],
    *,
    include_pair: Callable[[MathItem, MathItem], bool] | None = None,
) -> list[ContentFinding]:
    """Report each item whose mathematical core matches an earlier item.

    Questions (and lesson active-recall checks) match when their numbers, variables,
    operators, scenario words (code-selection prompts only) and canonical answers agree and
    their concept words do not contradict each other.  A lesson worked example has no answer
    field, so it matches a question of the same topic when the numbers appear in the same
    order and everything else except the answer agrees.  Lesson-to-lesson pairs are not
    compared.
    """

    findings = []
    strict: dict[tuple, list[MathItem]] = defaultdict(list)
    loose: dict[tuple, list[MathItem]] = defaultdict(list)
    reported: set[tuple[str, str]] = set()
    for item in items:
        signature = item.signature
        if signature.strength < 2 or not (signature.numbers or signature.words):
            continue
        candidates: list[MathItem] = []
        if signature.answer is not None:
            candidates.extend(strict[_strict_key(signature)])
        if len(signature.ordered_numbers) >= 2:
            candidates.extend(
                other
                for other in loose[_loose_key(signature)]
                if (other.signature.answer is None) != (signature.answer is None)
                and other not in candidates
            )
        for other in candidates:
            if other.subject == item.subject:
                continue
            if other.kind == "lesson" and item.kind == "lesson":
                continue
            if "lesson" in {other.kind, item.kind} and other.topic != item.topic:
                continue
            if not _concepts_compatible(other.signature, signature):
                continue
            if (
                other.topic != item.topic
                and signature.strength < 3
                and not set(other.signature.concepts) & set(signature.concepts)
            ):
                # Two numbers and an answer (3 x 4 = 12) are too common across topics to
                # count without a shared concept such as 'discount' or 'area'.
                continue
            if include_pair is not None and not include_pair(other, item):
                continue
            pair = (other.subject, item.subject)
            if pair in reported:
                continue
            reported.add(pair)
            core = ", ".join(_fmt(value) for value in signature.ordered_numbers[:8])
            details = [f"numbers {core}"] if core else []
            if signature.variables:
                details.append(f"variables {', '.join(signature.variables)}")
            if signature.words:
                details.append("same scenario wording")
            if signature.answer:
                details.append(f"answer {signature.answer.split(':', 1)[1]}")
            findings.append(
                ContentFinding(
                    "content_math_duplicate",
                    item.subject,
                    item.location,
                    f"Math-identical to {other.subject} {other.location} "
                    f"({'; '.join(details)}) once context sentences and notation are removed",
                )
            )
            break
        if signature.answer is not None:
            strict[_strict_key(signature)].append(item)
        loose[_loose_key(signature)].append(item)
    return findings


# --------------------------------------------------------------------------------------------
# Entry points
# --------------------------------------------------------------------------------------------


def _question_text_blocks(question: Question) -> Iterator[tuple[str, object]]:
    for index, block in enumerate(question.stem):
        yield f"stem[{index}]", block
    for part_index, part in enumerate(question.parts):
        for index, block in enumerate(part.prompt):
            yield f"parts[{part_index}].prompt[{index}]", block
        for hint_index, hint in enumerate(part.hints):
            for index, block in enumerate(hint.content):
                yield f"parts[{part_index}].hints[{hint_index}][{index}]", block
        for step_index, step in enumerate(part.solution):
            for index, block in enumerate(step.content):
                yield f"parts[{part_index}].solution[{step_index}][{index}]", block


def lint_question(question: Question) -> list[ContentFinding]:
    """Run every single-item check on one question."""

    document = question.model_dump(mode="json")
    blocks = list(_question_text_blocks(question))
    findings = control_character_findings(document, question.stable_key)
    findings += float_noise_findings(
        [(f"parts[{index}]", part.response) for index, part in enumerate(question.parts)],
        [(location, _block_text(block)) for location, block in blocks],
        question.stable_key,
    )
    findings += plain_text_math_findings(
        [(location, block.text) for location, block in blocks if block.type == "text"],
        question.stable_key,
    )
    findings += prompt_without_question_findings(
        [
            (
                f"parts[{index}].prompt",
                [_block_text(block) for block in [*question.stem, *part.prompt]],
            )
            for index, part in enumerate(question.parts)
        ],
        question.stable_key,
    )
    findings += hint_answer_findings(question)
    findings += answer_solution_findings(question)
    return findings


def _lesson_blocks(lesson) -> Iterator[tuple[str, object]]:
    for index, section in enumerate(lesson.sections):
        prefix = f"sections[{index}]"
        if section.type in {"explanation", "summary"}:
            for block_index, block in enumerate(section.blocks):
                yield f"{prefix}.blocks[{block_index}]", block
        elif section.type == "worked_example":
            for block_index, block in enumerate(section.prompt):
                yield f"{prefix}.prompt[{block_index}]", block
            for step_index, step in enumerate(section.steps):
                for block_index, block in enumerate(step.content):
                    yield f"{prefix}.steps[{step_index}][{block_index}]", block
        else:
            for block_index, block in enumerate(section.prompt):
                yield f"{prefix}.prompt[{block_index}]", block
            for block_index, block in enumerate(section.feedback):
                yield f"{prefix}.feedback[{block_index}]", block


def lint_lesson(lesson) -> list[ContentFinding]:
    """Run the single-item checks that apply to lesson notes."""

    document = lesson.model_dump(mode="json")
    blocks = list(_lesson_blocks(lesson))
    findings = control_character_findings(document, lesson.stable_key)
    findings += float_noise_findings(
        [
            (f"sections[{index}]", section.response)
            for index, section in enumerate(lesson.sections)
            if section.type == "active_recall"
        ],
        [(location, _block_text(block)) for location, block in blocks],
        lesson.stable_key,
    )
    findings += plain_text_math_findings(
        [(location, block.text) for location, block in blocks if block.type == "text"],
        lesson.stable_key,
    )
    findings += prompt_without_question_findings(
        [
            (
                f"sections[{index}].prompt ({section.stable_key})",
                [_block_text(block) for block in section.prompt],
            )
            for index, section in enumerate(lesson.sections)
            if section.type in {"active_recall", "worked_example"}
        ],
        lesson.stable_key,
    )
    return findings


def finding_counts(findings: Iterable[ContentFinding]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for finding in findings:
        counts[finding.code] += 1
    return dict(sorted(counts.items()))


def structural_warnings(report) -> list:
    """Warnings that are not content-lint findings (used where a report must stay clean)."""

    return [issue for issue in report.warnings if not is_content_lint_code(issue.code)]
