"""Deterministic, explainable candidate generation for the fixed taxonomy."""

import re
from dataclasses import dataclass, field

from .models import Evidence, Level, Taxonomy


@dataclass(frozen=True)
class Rule:
    topic: str
    pattern: str
    weight: float
    label: str
    outcome: str | None = None
    kind: str = "phrase"


@dataclass
class Candidate:
    topic_code: str
    score: float = 0
    confidence: float = 0
    evidence: list[Evidence] = field(default_factory=list)
    outcome_code: str | None = None
    outcome_score: float = 0


RULES = [
    Rule(
        "N1",
        r"\bprime factor(?:isation|ization)?\b|\bprime numbers?\b",
        4,
        "prime factorisation",
        "1.1",
    ),
    Rule(
        "N1",
        r"\b(?:hcf|highest common factor|lcm|lowest common multiple)\b",
        5,
        "HCF or LCM",
        "1.2",
    ),
    Rule("N1", r"\b(?:square|cube) roots?\b", 3, "roots", "1.2"),
    Rule("N1", r"\bnegative numbers?|rational numbers?|real numbers?\b", 3, "number sets", "1.3"),
    Rule("N1", r"\bnumber line\b|\border(?:ing)? numbers?\b", 3, "number line", "1.5"),
    Rule(
        "N1",
        r"\bround(?:ing)?\b|\bsignificant figures?\b|\bestimat(?:e|ion)\b|\bapproximation\b",
        4,
        "approximation",
        "1.7",
    ),
    Rule("N2", r"\bratios?\b", 3, "ratio", "2.3"),
    Rule("N2", r"\bsimplest (?:form )?ratio\b", 3, "simplest ratio", "2.2"),
    Rule("N2", r"\bmap scales?\b|\bscale drawing\b", 5, "map scale", "2.4"),
    Rule(
        "N2",
        r"\b(?:directly|direct|inversely|inverse) proportional\b|\b(?:direct|inverse) proportion\b",
        9,
        "direct or inverse proportion",
        "2.5",
    ),
    Rule("N2", r"\bworkers?\b.*\bdays?\b|\bmen\b.*\bdays?\b", 3, "work and time proportion", "2.5"),
    Rule("N3", r"\bpercent(?:age)?\b|%", 3, "percentage", "3.6"),
    Rule("N3", r"\bpercentage (?:increase|decrease|profit|loss)\b", 5, "percentage change", "3.6"),
    Rule(
        "N3", r"\bprofit\b|\bloss\b|\bdiscount\b|\bmarked price\b", 3, "financial percentage", "3.6"
    ),
    Rule(
        "N3",
        r"\breverse percentage\b|\boriginal (?:price|value|amount)\b",
        4,
        "reverse percentage",
        "3.5",
    ),
    Rule(
        "N3",
        r"\bincreas(?:e|ed) by .*%|\bdecreas(?:e|ed) by .*%",
        4,
        "percentage increase or decrease",
        "3.4",
    ),
    Rule("N4", r"\baverage speed\b|\bconstant speed\b", 5, "speed concept", "4.1"),
    Rule("N4", r"\b(?:km/h|km per hour|m/s|metres? per second)\b", 4, "speed unit", "4.2"),
    Rule("N4", r"\bdistance[- ]time\b|\bspeed[- ]time\b", 4, "motion graph", "4.3"),
    Rule(
        "N4",
        r"\b(?:find|calculate).*\bspeed\b|\brate of (?:flow|work|change)\b",
        3,
        "rate or speed problem",
        "4.3",
    ),
    Rule("N5", r"\balgebraic fractions?\b", 5, "algebraic fraction", "5.16"),
    Rule("N5", r"\bsingle fraction\b", 5, "single algebraic fraction", "5.16"),
    Rule(
        "N5",
        r"fraction.*(?:x|y|a|b).*(?:fraction|denominator)|(?:x|y|a|b).*denominator",
        3,
        "variable denominator",
        "5.16",
        "notation",
    ),
    Rule("N5", r"\bexpand\b|\bexpansion\b", 4, "expansion", "5.9"),
    Rule("N5", r"\bchange the subject\b", 5, "change the subject", "5.10"),
    Rule("N5", r"\bunknown quantity in (?:a|the) formula\b", 4, "unknown in formula", "5.11"),
    Rule(
        "N5",
        r"\balgebraic identit(?:y|ies)\b|a\s*squared\s*(?:minus|[-−])\s*b\s*squared|a\s*squared\s*(?:plus|\+)\s*b\s*squared",
        5,
        "algebraic identity",
        "5.12",
    ),
    Rule("N5", r"\bfactoris(?:e|ation)\b|\bfactoriz(?:e|ation)\b", 4, "factorisation", "5.13"),
    Rule("N5", r"\bquadratic expression\b.*\bfactor", 3, "quadratic factorisation", "5.14"),
    Rule("N5", r"\bnth term\b|\balgebraic pattern\b", 4, "algebraic pattern", "5.5"),
    Rule("N5", r"\bsimplif(?:y|ication)\b.*\bexpression\b", 3, "simplify expression", "5.7"),
    Rule(
        "N6", r"\bcartesian coordinates?\b|\bcoordinate plane\b", 4, "Cartesian coordinates", "6.1"
    ),
    Rule("N6", r"\blinear functions?\b", 4, "linear function", "6.3"),
    Rule("N6", r"\bgradient\b|\bslope\b", 4, "gradient", "6.5"),
    Rule(
        "N6",
        r"\bquadratic functions?\b|\bquadratic graph\b|\bparabola\b",
        6,
        "quadratic function",
        "6.6",
    ),
    Rule(
        "N6",
        r"\bmaximum point\b|\bminimum point\b|\baxis of symmetry\b",
        7,
        "quadratic graph property",
        "6.7",
    ),
    Rule(
        "N6",
        r"\bgraph\b.*\b(?:x-axis|y-axis|curve|equation)\b|\b(?:x-axis|y-axis)\b.*\bgraph\b",
        4,
        "function graph",
        "6.7",
    ),
    Rule(
        "N7",
        r"\bsimultaneous (?:linear )?equations?\b|\bsubstitution and elimination\b",
        6,
        "simultaneous equations",
        "7.8",
    ),
    Rule("N7", r"\bquadratic equations?\b.*\bfactor", 5, "quadratic equation", "7.9"),
    Rule(
        "N7",
        r"\binequalit(?:y|ies)\b|(?:≤|>=|<=|≥).*(?:x|y)|(?:x|y).*(?:≤|>=|<=|≥)",
        5,
        "inequality",
        "7.6",
        "notation",
    ),
    Rule("N7", r"\bsolve (?:for )?[a-z]\b|\bsolve the equation\b", 3, "solve equation", "7.2"),
    Rule("N7", r"\blinear equation\b", 3, "linear equation", "7.2"),
    Rule("G1", r"\b(?:pentagon|hexagon|octagon|polygon)\b", 5, "polygon", "1.6"),
    Rule("G1", r"\binterior angles?\b|\bexterior angles?\b", 5, "polygon angle", "1.6"),
    Rule(
        "G1",
        r"\bparallel lines?\b.*\bangles?\b|\bcorresponding angles?\b|\balternate angles?\b",
        5,
        "parallel-line angles",
        "1.3",
    ),
    Rule(
        "G1",
        r"\bvertically opposite\b|\bangles? on a straight line\b",
        4,
        "basic angle property",
        "1.2",
    ),
    Rule(
        "G1",
        r"\b(?:triangle|quadrilateral|trapezium|parallelogram)\b.*\bangles?\b",
        4,
        "shape angle property",
        "1.4",
    ),
    Rule(
        "G1",
        r"\bconstruct(?:ion)?\b.*\b(?:compass|protractor|set square|ruler)\b",
        5,
        "geometric construction",
        "1.7",
    ),
    Rule("G2", r"\bcongruen(?:t|ce)\b", 5, "congruence", "2.1"),
    Rule(
        "G2",
        r"\bsimilar (?:figures?|triangles?|polygons?)\b|\b(?:figures?|triangles?|polygons?) (?:are )?similar\b|\bsimilarity\b",
        5,
        "similarity",
        "2.3",
    ),
    Rule(
        "G2",
        r"\benlargement\b|\breduction\b.*\bfigure\b|\bscale factor\b",
        5,
        "enlargement or reduction",
        "2.4",
    ),
    Rule(
        "G4", r"\bpythagoras(?:'|’)?(?: theorem)?\b|\bpythagorean\b", 6, "Pythagoras theorem", "4.1"
    ),
    Rule(
        "G4",
        r"\bright[- ]angled triangle\b.*\b(?:three )?sides?\b",
        4,
        "right-angle side test",
        "4.2",
    ),
    Rule(
        "G4",
        r"\b(?:sine|cosine|tangent)\b|\b(?:sin|cos|tan)\s*(?:\(|\d)",
        5,
        "trigonometric ratio",
        "4.3",
    ),
    Rule(
        "G5",
        r"\bperimeter\b|\barea of (?:a |the )?(?:parallelogram|trapezium)\b",
        4,
        "plane mensuration",
        "5.1",
    ),
    Rule("G5", r"\bcomposite plane figures?\b", 5, "composite plane figure", "5.2"),
    Rule(
        "G5", r"\b(?:volume|surface area)\b.*\b(?:prism|cylinder)\b", 5, "prism or cylinder", "5.3"
    ),
    Rule(
        "G5",
        r"\b(?:volume|surface area)\b.*\b(?:pyramid|cone|sphere)\b",
        6,
        "pyramid, cone or sphere",
        "5.6",
    ),
    Rule("G5", r"\bcomposite solids?\b", 5, "composite solid", "5.5"),
    Rule(
        "S1",
        r"\b(?:bar|line|pie) graphs?\b|\bpictograms?\b|\bpie charts?\b",
        4,
        "statistical graph",
        "1.2",
    ),
    Rule(
        "S1",
        r"\b(?:dot diagrams?|histograms?|stem[- ]and[- ]leaf)\b",
        5,
        "Secondary Two statistical diagram",
        "1.5",
    ),
    Rule("S1", r"\bmean\b|\bmedian\b|\bmode\b|\bcentral tendency\b", 4, "central tendency", "1.8"),
    Rule("S1", r"\bgrouped data\b", 7, "grouped data mean", "1.10"),
    Rule(
        "S1", r"\bcollecting data\b|\btabulating data\b|\bdata table\b", 3, "data handling", "1.1"
    ),
    Rule(
        "S1",
        r"\bmisleading (?:graph|diagram|data)\b|\bmisinterpretation of data\b",
        5,
        "misleading statistics",
        "1.4",
    ),
    Rule("S2", r"\bprobabilit(?:y|ies)\b|\bmeasure of chance\b", 5, "probability", "2.1"),
    Rule(
        "S2",
        r"\bpossible outcomes?\b|\bsample space\b|\bsingle events?\b",
        7,
        "single-event outcomes",
        "2.2",
    ),
]

COMPILED_RULES = [(rule, re.compile(rule.pattern, re.I | re.S)) for rule in RULES]


def normalize(content: str) -> str:
    replacements = {
        r"\leq": "≤",
        r"\le": "≤",
        r"\geq": "≥",
        r"\ge": "≥",
        r"\angle": " angle ",
        r"\circ": " degrees ",
        r"\frac": " fraction ",
        r"^{2}": " squared ",
        r"^2": " squared ",
    }
    value = content.lower()
    for old, new in replacements.items():
        value = value.replace(old.lower(), new)
    value = re.sub(r"[{}$\\]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


class RuleClassifier:
    def __init__(
        self,
        taxonomy: Taxonomy,
        *,
        minimum_score: float = 3.0,
        minimum_margin: float = 0.75,
    ):
        self.taxonomy = taxonomy
        self.minimum_score = minimum_score
        self.minimum_margin = minimum_margin

    def classify(self, content: str, source_level: Level | None = None) -> list[Candidate]:
        normalized = normalize(content)
        candidates = {
            topic.code: Candidate(topic_code=topic.code) for topic in self.taxonomy.topics
        }
        outcome_scores: dict[str, dict[str, float]] = {code: {} for code in candidates}
        for rule, pattern in COMPILED_RULES:
            match = pattern.search(normalized)
            if not match:
                continue
            candidate = candidates[rule.topic]
            candidate.score += rule.weight
            candidate.evidence.append(
                Evidence(
                    kind=rule.kind,
                    value=f"{rule.label}: {match.group(0)[:120]}",
                    weight=rule.weight,
                    outcome_code=rule.outcome,
                )
            )
            if rule.outcome:
                outcome_scores[rule.topic][rule.outcome] = (
                    outcome_scores[rule.topic].get(rule.outcome, 0) + rule.weight
                )

        ranked = sorted(candidates.values(), key=lambda candidate: candidate.score, reverse=True)
        top = ranked[0]
        runner_up = ranked[1]
        if top.score < self.minimum_score or top.score - runner_up.score < self.minimum_margin:
            return []

        selected = [top]
        selected.extend(
            candidate
            for candidate in ranked[1:]
            if candidate.score >= 3 and candidate.score >= top.score * 0.4
        )
        selected = selected[:3]
        primary_confidence = 0.0
        for index, candidate in enumerate(selected):
            margin = candidate.score - (runner_up.score if index == 0 else 0)
            if index == 0:
                candidate.confidence = min(
                    0.99,
                    0.5 + min(candidate.score, 8) * 0.045 + max(0, min(margin, 3)) * 0.04,
                )
                primary_confidence = candidate.confidence
            else:
                candidate.confidence = min(
                    primary_confidence - 0.05,
                    0.45 + min(candidate.score, 8) * 0.045,
                )
            scores = outcome_scores[candidate.topic_code]
            if scores:
                candidate.outcome_code, candidate.outcome_score = max(
                    scores.items(), key=lambda item: item[1]
                )
                levels = {
                    outcome.level
                    for outcome in self.taxonomy.outcomes
                    if outcome.topic_id
                    == next(t.id for t in self.taxonomy.topics if t.code == candidate.topic_code)
                    and outcome.code == candidate.outcome_code
                }
                if source_level and source_level in levels:
                    candidate.evidence.append(
                        Evidence(
                            kind="level",
                            value=source_level,
                            weight=0.25,
                            outcome_code=candidate.outcome_code,
                        )
                    )
        return selected
