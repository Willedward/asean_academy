"""Founder-supplied G3 Mathematics Secondary One and Two syllabus subset."""

from uuid import NAMESPACE_URL, uuid5

from .models import TAXONOMY_VERSION, Outcome, Taxonomy, Topic

TOPICS = [
    ("N1", "number_and_algebra", "Numbers and their operations"),
    ("N2", "number_and_algebra", "Ratio and proportion"),
    ("N3", "number_and_algebra", "Percentage"),
    ("N4", "number_and_algebra", "Rate and Speed"),
    ("N5", "number_and_algebra", "Algebraic expressions and formulae"),
    ("N6", "number_and_algebra", "Functions and graphs"),
    ("N7", "number_and_algebra", "Equations and inequalities"),
    ("G1", "geometry_and_measurement", "Angles, triangles and polygons"),
    ("G2", "geometry_and_measurement", "Congruence and similarity"),
    ("G4", "geometry_and_measurement", "Pythagoras' theorem and trigonometry"),
    ("G5", "geometry_and_measurement", "Mensuration"),
    ("S1", "statistics_and_probability", "Data handling and analysis"),
    ("S2", "statistics_and_probability", "Probability"),
]

OUTCOMES = {
    "secondary_1": {
        "N1": [
            ("1.1", "primes and prime factorisation"),
            (
                "1.2",
                "finding HCF and LCM, squares, cubes, square roots and cube roots by prime factorisation",
            ),
            (
                "1.3",
                "negative numbers, integers, rational numbers, real numbers and their four operations",
            ),
            ("1.4", "calculations with calculator"),
            ("1.5", "representation and ordering of numbers on the number line"),
            ("1.6", "use of <, >, <= and >="),
            ("1.7", "approximation and estimation, including rounding and significant figures"),
        ],
        "N2": [
            ("2.1", "ratios involving rational numbers"),
            ("2.2", "writing a ratio in its simplest form"),
            ("2.3", "problems involving ratio"),
        ],
        "N3": [
            ("3.1", "expressing one quantity as a percentage of another"),
            ("3.2", "comparing two quantities by percentage"),
            ("3.3", "percentages greater than 100%"),
            ("3.4", "increasing or decreasing a quantity by a given percentage"),
            ("3.5", "reverse percentages"),
            ("3.6", "problems involving percentages"),
        ],
        "N4": [
            ("4.1", "concepts of average rate, speed, constant speed and average speed"),
            ("4.2", "conversion of units such as kilometres per hour to metres per second"),
            ("4.3", "problems involving rate and speed"),
        ],
        "N5": [
            ("5.1", "using letters to represent numbers"),
            ("5.2", "interpreting algebraic notation"),
            ("5.3", "evaluation of algebraic expressions and formulae"),
            ("5.4", "translation of simple real-world situations into algebraic expressions"),
            (
                "5.5",
                "recognising and representing patterns and finding an expression for the nth term",
            ),
            ("5.6", "addition and subtraction of linear expressions"),
            ("5.7", "simplification of linear expressions"),
            ("5.8", "use of brackets and extraction of common factors"),
        ],
        "N6": [
            ("6.1", "Cartesian coordinates in two dimensions"),
            ("6.2", "graph of ordered pairs as a relationship between two variables"),
            ("6.3", "linear functions"),
            ("6.4", "graphs of linear functions"),
            ("6.5", "gradient of a linear graph as a ratio of vertical to horizontal change"),
        ],
        "N7": [
            ("7.1", "concept of equation"),
            ("7.2", "solving linear equations in one variable"),
            ("7.3", "solving simple fractional equations reducible to linear equations"),
            ("7.4", "formulating a linear equation in one variable to solve problems"),
        ],
        "G1": [
            ("1.1", "right, acute, obtuse and reflex angles"),
            ("1.2", "vertically opposite angles, angles on a straight line and angles at a point"),
            ("1.3", "angles formed by parallel lines and a transversal"),
            ("1.4", "properties of triangles, special quadrilaterals and regular polygons"),
            ("1.5", "classifying special quadrilaterals by their properties"),
            ("1.6", "angle sum of interior and exterior angles of any convex polygon"),
            ("1.7", "construction of simple geometric figures from given data"),
        ],
        "G5": [
            ("5.1", "area of a parallelogram and trapezium"),
            ("5.2", "perimeter and area of composite plane figures"),
            ("5.3", "volume and surface area of prism and cylinder"),
            ("5.4", "conversion between square and cubic metric units"),
            ("5.5", "volume and surface area of composite solids"),
        ],
        "S1": [
            ("1.1", "collecting, classifying and tabulating data"),
            ("1.2", "analysis and interpretation of tables and common statistical graphs"),
            ("1.3", "purposes, uses, advantages and disadvantages of statistical representations"),
            ("1.4", "explaining why a statistical diagram leads to misinterpretation of data"),
        ],
    },
    "secondary_2": {
        "N2": [
            ("2.4", "map scales involving distance and area"),
            ("2.5", "direct and inverse proportion"),
        ],
        "N5": [
            ("5.9", "expansion of the product of algebraic expressions"),
            ("5.10", "changing the subject of a formula"),
            ("5.11", "finding the value of an unknown quantity in a formula"),
            ("5.12", "use of standard algebraic identities"),
            ("5.13", "factorisation of linear expressions"),
            ("5.14", "factorisation of quadratic expressions"),
            ("5.15", "multiplication and division of simple algebraic fractions"),
            (
                "5.16",
                "addition and subtraction of algebraic fractions with linear or quadratic denominators",
            ),
        ],
        "N6": [
            ("6.6", "quadratic functions"),
            ("6.7", "graphs of quadratic functions and their properties"),
        ],
        "N7": [
            ("7.5", "concept of equation and inequality"),
            (
                "7.6",
                "solving simple linear inequalities and representing solutions on a number line",
            ),
            ("7.7", "graphs of linear equations in two variables"),
            ("7.8", "solving simultaneous linear equations in two variables"),
            ("7.9", "solving quadratic equations by factorisation"),
            ("7.10", "formulating a pair of linear equations in two variables to solve problems"),
        ],
        "G2": [
            ("2.1", "congruent figures"),
            ("2.2", "similar figures"),
            ("2.3", "properties of similar triangles and polygons"),
            ("2.4", "enlargement and reduction of a plane figure"),
            ("2.5", "problems involving congruence and similarity"),
        ],
        "G4": [
            ("4.1", "use of Pythagoras' theorem"),
            ("4.2", "determining whether a triangle is right-angled from three side lengths"),
            ("4.3", "use of sine, cosine and tangent in right-angled triangles"),
        ],
        "G5": [("5.6", "volume and surface area of pyramid, cone and sphere")],
        "S1": [
            (
                "1.5",
                "analysis and interpretation of dot diagrams, histograms and stem-and-leaf diagrams",
            ),
            ("1.6", "purposes, uses, advantages and disadvantages of statistical representations"),
            ("1.7", "explaining why a statistical diagram leads to misinterpretation of data"),
            ("1.8", "mean, mode and median as measures of central tendency for a set of data"),
            ("1.9", "purposes and use of mean, mode and median"),
            ("1.10", "calculation of the mean for grouped data"),
        ],
        "S2": [
            ("2.1", "probability as a measure of chance"),
            ("2.2", "probability of single events and listing possible outcomes"),
        ],
    },
}


def stable_id(kind: str, *parts: str):
    return uuid5(NAMESPACE_URL, ":".join(("asean-academy", TAXONOMY_VERSION, kind, *parts)))


def load_taxonomy() -> Taxonomy:
    topics = [
        Topic(id=stable_id("topic", code), code=code, strand=strand, name=name, order=order)
        for order, (code, strand, name) in enumerate(TOPICS)
    ]
    topic_ids = {topic.code: topic.id for topic in topics}
    outcomes = []
    order = 0
    for level, topic_groups in OUTCOMES.items():
        for topic_code, entries in topic_groups.items():
            for code, description in entries:
                outcomes.append(
                    Outcome(
                        id=stable_id("outcome", level, topic_code, code),
                        topic_id=topic_ids[topic_code],
                        level=level,
                        code=code,
                        description=description,
                        order=order,
                    )
                )
                order += 1
    return Taxonomy(
        version=TAXONOMY_VERSION,
        title="G3 Mathematics Secondary One and Two syllabus subset",
        status="draft",
        source_reference="Founder-supplied syllabus images, 16 September 2026",
        topics=topics,
        outcomes=outcomes,
    )
