import pytest

from question_categorizer.rules import RuleClassifier
from question_categorizer.taxonomy import load_taxonomy


def test_taxonomy_has_supplied_topics_and_outcomes():
    taxonomy = load_taxonomy()
    assert [topic.code for topic in taxonomy.topics] == [
        "N1",
        "N2",
        "N3",
        "N4",
        "N5",
        "N6",
        "N7",
        "G1",
        "G2",
        "G4",
        "G5",
        "S1",
        "S2",
    ]
    assert len(taxonomy.outcomes) == 87
    assert taxonomy.status == "draft"


@pytest.mark.parametrize(
    ("content", "topic", "outcome"),
    [
        ("Find the HCF and LCM of the following numbers.", "N1", "1.2"),
        ("The map scale is 1 : 50 000.", "N2", "2.4"),
        ("Find the percentage profit after the discount.", "N3", "3.6"),
        ("Calculate the average speed in km/h.", "N4", "4.1"),
        ("Express the algebraic fractions as a single fraction.", "N5", "5.16"),
        ("Find the maximum point of the quadratic graph.", "N6", "6.7"),
        ("Solve the simultaneous linear equations.", "N7", "7.8"),
        ("Find the sum of the interior angles of the pentagon.", "G1", "1.6"),
        ("The two triangles are similar. Find the scale factor.", "G2", "2.3"),
        ("Use Pythagoras' theorem to find the missing side.", "G4", "4.1"),
        ("Find the volume and surface area of the cone.", "G5", "5.6"),
        ("Calculate the mean from the histogram of grouped data.", "S1", "1.10"),
        ("List the possible outcomes and calculate the probability.", "S2", "2.2"),
    ],
)
def test_rules_classify_representative_questions(content, topic, outcome):
    candidates = RuleClassifier(load_taxonomy()).classify(content, "secondary_2")
    assert candidates[0].topic_code == topic
    assert candidates[0].outcome_code == outcome
    assert candidates[0].evidence


def test_fixed_subset_does_not_force_circle_theorem_into_g1():
    candidates = RuleClassifier(load_taxonomy()).classify(
        "O is the centre of the circle. Find angle ABC using the circle theorem."
    )
    assert candidates == []


def test_inverse_proportion_is_primary_and_percentage_is_secondary():
    candidates = RuleClassifier(load_taxonomy()).classify(
        "If y is inversely proportional to x, find the percentage decrease in y."
    )
    assert [candidate.topic_code for candidate in candidates[:2]] == ["N2", "N3"]
    assert candidates[1].confidence < candidates[0].confidence


def test_person_named_tan_is_not_trigonometry():
    candidates = RuleClassifier(load_taxonomy()).classify(
        "Mr Tan deposited $1500 at 2% per annum compound interest."
    )
    assert candidates[0].topic_code == "N3"
    assert all(candidate.topic_code != "G4" for candidate in candidates)
