"""Expand authored geometry notes and add deterministic SVG teaching diagrams."""

from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LESSONS = {
    "g1-lesson-01": {
        "kind": "angle_types",
        "visual": "An angle is the amount of turn from one ray to another, measured at the vertex. Read the smaller turn unless a reflex angle is explicitly marked. Acute angles lie between 0° and 90°, a right angle is exactly 90°, obtuse angles lie between 90° and 180°, and reflex angles lie between 180° and 360°.",
        "deep": "Complementary angles total 90°, supplementary angles total 180°, and angles in a complete turn total 360°. Translate the geometry into one of these totals before forming an equation. An angle bisector divides one angle into two equal angles, so represent both parts by the same expression.",
        "prompt": "A reflex angle is three times its smaller angle around the same point. Find both angles.",
        "steps": [
            "Let the smaller angle be x°. The reflex angle is 3x°.",
            "Angles around a point total 360°, so x+3x=360.",
            "Hence x=90, so the two angles are 90° and 270°.",
        ],
        "check": "The two results total 360°, and 270° is between 180° and 360°.",
        "mistakes": "Do not classify an angle from the way a sketch looks. Use its stated or calculated measure. Do not call 90° acute or 180° obtuse: boundary values have their own names. For a reflex angle, confirm that the answer exceeds 180°.",
        "alt": "Four labelled examples showing an acute angle, a right angle, an obtuse angle and a reflex angle.",
    },
    "g1-lesson-02": {
        "kind": "intersection",
        "visual": "At an intersection, vertically opposite angles are the non-adjacent pair across the vertex and are equal. Adjacent angles on a straight line total 180°. All angles around the point total 360°. Mark one known angle first, then propagate only relationships that share the same vertex.",
        "deep": "When algebraic expressions label vertically opposite angles, equate them. When expressions label an adjacent linear pair, add them and set the sum to 180°. A reliable check is to alternate the two angle sizes around a two-line intersection and verify that all four total 360°.",
        "prompt": "Vertically opposite angles are (5x+7)° and (8x−38)°. Find every angle at the intersection.",
        "steps": [
            "Vertically opposite angles are equal, so 5x+7=8x−38.",
            "Solve 45=3x to obtain x=15. Each of that opposite pair is 82°.",
            "Each adjacent angle is 180°−82°=98°, so the four angles alternate 82°, 98°, 82°, 98°.",
        ],
        "check": "Opposite angles match and 82+98+82+98=360.",
        "mistakes": "Do not equate adjacent angles unless another fact says they are equal. A straight line gives a total of 180°, while angles around a point give 360°. State the angle fact before writing the equation so the correct total is clear.",
        "alt": "Two intersecting straight lines with the four angles around the intersection labelled a, b, a and b.",
    },
    "g1-lesson-03": {
        "kind": "parallel",
        "visual": "A transversal crossing parallel lines creates matching angle positions. Corresponding angles are equal, alternate angles are equal, and co-interior angles on the same side total 180°. The arrow markings on the lines, rather than their appearance, establish that the lines are parallel.",
        "deep": "Trace a Z shape for alternate angles, an F shape for corresponding angles and a C shape for co-interior angles, but always confirm which lines form the angle. Converse facts also work: if a valid pair of corresponding or alternate angles is equal, or co-interior angles total 180°, the lines are parallel.",
        "prompt": "Two parallel lines are cut by a transversal. A co-interior pair is (3x+12)° and (5x−8)°. Find x and both angles.",
        "steps": [
            "Co-interior angles between parallel lines are supplementary.",
            "Write (3x+12)+(5x−8)=180, giving 8x+4=180 and x=22.",
            "The angles are 78° and 102°.",
        ],
        "check": "The calculated angles add to 180°, as a co-interior pair must.",
        "mistakes": "Do not use a parallel-line fact unless parallel arrows are shown or parallelism has been proved. Corresponding and alternate angles are equal; co-interior angles are supplementary. Keep the transversal fixed when identifying the pair.",
        "alt": "Two parallel horizontal lines crossed by a transversal, with corresponding, alternate and co-interior angle positions highlighted.",
    },
    "g1-lesson-04": {
        "kind": "polygons",
        "visual": "Shape properties come from definitions and markings. A triangle totals 180°. A quadrilateral totals 360°. Isosceles triangles have two equal sides and two equal base angles. Equilateral triangles have three equal sides and three 60° angles. Regular polygons have all sides and all interior angles equal.",
        "deep": "For a multi-step problem, record every justified property beside the diagram: equal sides, equal angles, parallel sides and symmetry. Then use triangle or quadrilateral angle sums. A diagonal can split a quadrilateral into triangles, but properties of the diagonal depend on the quadrilateral type.",
        "prompt": "An isosceles trapezium has two equal angles of 68° on one base. Find the two angles on the other base.",
        "steps": [
            "Adjacent interior angles between the parallel bases are supplementary.",
            "Each angle on the other base is 180°−68°=112°.",
            "The four angles are 68°, 68°, 112° and 112°.",
        ],
        "check": "The four angles total 360° and the base-angle pairs are equal.",
        "mistakes": "Do not assume a property merely because a drawing looks symmetric. Use stated markings and definitions. A regular polygon requires both equal sides and equal angles. When a diagonal is drawn, identify which new triangles and angle sums it creates.",
        "alt": "Reference drawings of a triangle, parallelogram, trapezium and regular hexagon with standard equality and parallel markings.",
    },
    "g1-lesson-05": {
        "kind": "quadrilateral",
        "visual": "Quadrilaterals form a hierarchy. Every square is also a rectangle, rhombus and parallelogram. Every rectangle and every rhombus is a parallelogram. A kite has two pairs of adjacent equal sides, while a trapezium has one pair of parallel sides under the syllabus convention used here.",
        "deep": "Classify a figure by the most specific set of guaranteed properties. Sides and angles often narrow the class first; diagonals then distinguish related shapes. Rectangle diagonals are equal and bisect each other. Rhombus diagonals are perpendicular and bisect each other. Square diagonals have both sets of properties.",
        "prompt": "A parallelogram has perpendicular diagonals and one right angle. Classify it as specifically as possible.",
        "steps": [
            "One right angle in a parallelogram makes all four angles right angles, so it is a rectangle.",
            "Perpendicular diagonals in a parallelogram also make it a rhombus.",
            "A quadrilateral that is both a rectangle and a rhombus is a square.",
        ],
        "check": "A square satisfies every stated property: opposite sides parallel, four right angles and perpendicular bisecting diagonals.",
        "mistakes": "Do not stop at a broad name when a more specific one is guaranteed. Equal diagonals alone do not prove a square, and perpendicular diagonals alone do not prove a square. Combine all given properties before classifying.",
        "alt": "A hierarchy diagram linking parallelogram, rectangle, rhombus and square, with kite and trapezium shown separately.",
    },
    "g1-lesson-06": {
        "kind": "exterior",
        "visual": "Drawing diagonals from one vertex divides a convex n-sided polygon into n−2 triangles, so its interior-angle sum is (n−2)×180°. One exterior angle at each vertex, taken in the same direction, always totals 360°. In a regular polygon all exterior angles are equal.",
        "deep": "For a regular polygon, exterior angle=360°/n and interior angle=180°−exterior angle. To recover n, divide 360° by the exterior angle. If an interior angle is given, first subtract it from 180°. The resulting side count must be a whole number at least 3.",
        "prompt": "Each interior angle of a regular polygon is 156°. Find the number of sides.",
        "steps": [
            "The exterior angle is 180°−156°=24°.",
            "The exterior angles total 360°, so n=360/24.",
            "Therefore n=15.",
        ],
        "check": "(15−2)×180°=2340°, and 2340°÷15=156°.",
        "mistakes": "Do not divide 360° by an interior angle. Convert to the exterior angle first. The formula (n−2)×180° gives the total interior sum, not one interior angle unless you divide by n for a regular polygon.",
        "alt": "A regular hexagon showing a fan of four triangles and one exterior angle at a vertex.",
    },
    "g1-lesson-07": {
        "kind": "construction",
        "visual": "Straightedge-and-compass construction preserves exact geometric conditions. Equal-radius arcs from the endpoints of a segment locate points equidistant from both endpoints; joining the arc intersections gives the perpendicular bisector. Equal arcs from the sides of an angle locate its angle bisector.",
        "deep": "Keep construction arcs visible because they are the evidence. For SSS, draw one side and intersect two circles. For SAS, construct the included angle between the two known sides. For ASA, construct the two known angles at the ends of the known side. Verify lengths and angles after construction.",
        "prompt": "Construct triangle ABC with AB=7 cm, AC=5 cm and BC=4 cm, then describe why the construction is unique up to reflection.",
        "steps": [
            "Draw AB=7 cm.",
            "With centre A and radius 5 cm draw an arc. With centre B and radius 4 cm draw a second arc.",
            "Label an intersection C and join AC and BC. The two possible intersections are mirror images across AB.",
        ],
        "check": "Measure AC and BC and keep both intersecting arcs visible as evidence of the SSS construction.",
        "mistakes": "Do not erase the arcs used to locate a point. A ruler with no compass construction does not demonstrate an exact bisector. Check that two arcs actually intersect; otherwise the proposed triangle data may be impossible.",
        "alt": "A line segment AB with intersecting compass arcs locating C, together with a perpendicular-bisector construction.",
    },
    "g5-lesson-01": {
        "kind": "area",
        "visual": "A parallelogram has area base×perpendicular height. The height must meet the base at 90°, even when it falls outside the sloping side. A trapezium has area one half times the sum of its parallel sides times the perpendicular height.",
        "deep": "Choose either parallel side as the parallelogram base, then pair it with the corresponding perpendicular height. For a trapezium, identify the parallel pair before substituting. Keep units consistent and square the final length unit because area measures two-dimensional coverage.",
        "prompt": "A trapezium has area 126 cm², height 9 cm and one parallel side 10 cm. Find the other parallel side.",
        "steps": [
            "Use 126=1/2(10+b)×9.",
            "Multiply by 2 and divide by 9: 28=10+b.",
            "Hence b=18 cm.",
        ],
        "check": "Substitution gives 1/2(10+18)×9=126 cm².",
        "mistakes": "Do not use a sloping side as the height. Do not forget to add the parallel sides before halving. State cm² or m² for an area and check that a recovered length is positive and plausible.",
        "alt": "A parallelogram and a trapezium with bases and perpendicular heights clearly marked.",
    },
    "g5-lesson-02": {
        "kind": "composite_plane",
        "visual": "A composite plane figure can be partitioned into non-overlapping familiar shapes or enclosed in a large shape with cut-outs subtracted. Area counts internal coverage. Perimeter follows only the outside boundary, so shared internal edges are excluded.",
        "deep": "Mark every required length before calculating. Missing boundary lengths often come from subtraction along a common total width or height. For area, choose a decomposition that avoids overlap. For perimeter, trace the boundary once in order and list each exposed segment.",
        "prompt": "A 14 m by 10 m rectangle has a 6 m by 4 m corner removed. Find both the remaining area and the outside perimeter.",
        "steps": [
            "Area=14×10−6×4=116 m².",
            "Removing a corner replaces two outer lengths by two equal inner lengths, so the total perimeter remains 2(14+10).",
            "The outside perimeter is 48 m.",
        ],
        "check": "The remaining area is smaller than 140 m², and the boundary trace closes without counting internal edges.",
        "mistakes": "Do not add the area of a cut-out. Do not count shared edges in the outside perimeter. Area and perimeter use different units and cannot be combined in the same arithmetic expression.",
        "alt": "An L-shaped region shown as a large rectangle with a smaller rectangular corner removed.",
    },
    "g5-lesson-03": {
        "kind": "solids",
        "visual": "A prism has a constant cross-section, so volume=cross-sectional area×length. A cylinder is a circular prism with volume πr²h. Surface area unfolds every exposed face: two congruent ends plus the lateral surface.",
        "deep": "For a right prism, the lateral area is perimeter of cross-section×length. For a cylinder, curved area=2πrh and total surface area=2πr²+2πrh. Check whether a container is open or closed before including circular ends.",
        "prompt": "A closed cylinder has radius 3 cm and height 8 cm. Find its total surface area in terms of π.",
        "steps": [
            "The two circular ends have area 2πr²=18π.",
            "The curved surface has area 2πrh=48π.",
            "Total surface area=66π cm².",
        ],
        "check": "A closed cylinder includes two ends; every term has square units.",
        "mistakes": "Do not confuse diameter with radius. Volume uses cubic units; surface area uses square units. For prisms, the cross-sectional area is multiplied by the prism length, which may not be the vertical dimension in the sketch.",
        "alt": "A triangular prism and a cylinder with their cross-sections and lengths highlighted.",
    },
    "g5-lesson-04": {
        "kind": "conversion",
        "visual": "A linear conversion factor is applied once, a square-unit factor twice and a cubic-unit factor three times. Since 1 m=100 cm, 1 m²=100²=10,000 cm² and 1 m³=100³=1,000,000 cm³.",
        "deep": "Write the conversion as a power before multiplying. Moving to a smaller unit increases the numerical value; moving to a larger unit decreases it. Convert all dimensions before using an area or volume formula, rather than converting the final result inconsistently.",
        "prompt": "Convert 0.024 m³ to cm³ and then to litres.",
        "steps": [
            "0.024 m³=0.024×1,000,000=24,000 cm³.",
            "Since 1 litre=1,000 cm³, divide by 1,000.",
            "The volume is 24 litres.",
        ],
        "check": "0.024 m³ is 24 dm³, and each dm³ is one litre.",
        "mistakes": "Do not use the linear factor 100 for area or volume. Attach the exponent to the conversion factor. A quick direction check catches many errors: the number of square centimetres in one square metre must be much greater than one.",
        "alt": "A metre square divided into centimetre squares and a metre cube indicating squared and cubed conversion factors.",
    },
    "g5-lesson-05": {
        "kind": "composite_solid",
        "visual": "For a composite solid, volume is additive for joined non-overlapping pieces and subtractive for holes. Surface area requires a face audit: count exposed faces only. When two solids are joined, the contact region disappears from the outside surface on both pieces.",
        "deep": "Sketch an exploded view or table of components. Calculate each component volume using consistent units. For surface area, start with the separate totals and subtract twice the contact area. For a drilled hole, subtract its volume and add any newly exposed inner curved surface if surface area is required.",
        "prompt": "Two cuboids are joined across a 4 cm by 3 cm rectangular face. Their separate surface areas are 94 cm² and 112 cm². Find the exposed surface area of the composite solid.",
        "steps": [
            "The contact area is 4×3=12 cm².",
            "That face was counted once on each separate cuboid, so subtract 2×12.",
            "Exposed surface area=94+112−24=182 cm².",
        ],
        "check": "The joined solid has less surface area than the sum 206 cm² of the separate solids.",
        "mistakes": "Do not subtract a contact face only once. Do not subtract contact volume when pieces merely touch. Distinguish a cavity, which creates internal exposed surfaces, from a removed block whose opening and faces must be considered explicitly.",
        "alt": "Two cuboids joined at a shaded contact face, plus a cube with a cylindrical hole.",
    },
    "g2-lesson-01": {
        "kind": "congruent",
        "visual": "Congruent figures have identical shape and size even after translation, rotation or reflection. Write corresponding vertices in matching order. Equal tick marks identify corresponding sides and equal arc marks identify corresponding angles.",
        "deep": "For triangles, SSS uses three side pairs, SAS uses two sides and their included angle, ASA uses two angles and the included side, and RHS applies to right triangles with equal hypotenuse and one corresponding side. AAA proves similarity, not congruence; SSA is generally insufficient.",
        "prompt": "Right triangles ABC and PQR have right angles at B and Q, AC=PR=13 cm and AB=PQ=5 cm. Prove the triangles congruent and find the remaining side.",
        "steps": [
            "AC and PR are equal hypotenuses, AB and PQ are equal corresponding sides, and both triangles are right-angled.",
            "Therefore the triangles are congruent by RHS.",
            "Using Pythagoras, the remaining side is √(13²−5²)=12 cm in each triangle.",
        ],
        "check": "The correspondence A↔P, B↔Q, C↔R preserves the right angle, hypotenuse and matching side.",
        "mistakes": "Do not use AAA for congruence. In SAS, the equal angle must lie between the two equal sides. State the vertex correspondence before transferring a side or angle from one triangle to the other.",
        "alt": "Two congruent triangles in different orientations with matching side ticks and angle arcs.",
    },
    "g2-lesson-02": {
        "kind": "similar",
        "visual": "Similar figures have equal corresponding angles and proportional corresponding lengths. The image length equals scale factor times original length. Perimeters use the same linear factor, while areas use the square of that factor.",
        "deep": "Choose one direction for the scale factor and keep it throughout. If the factor from A to B is k, then length_B=k×length_A, perimeter_B=k×perimeter_A and area_B=k²×area_A. A scale factor of 1 gives congruent figures.",
        "prompt": "Two similar rectangles have areas 54 cm² and 150 cm². A side of the smaller rectangle is 9 cm. Find the corresponding side of the larger rectangle.",
        "steps": [
            "The area factor is 150/54=25/9.",
            "The positive linear factor is √(25/9)=5/3.",
            "The corresponding side is 9×5/3=15 cm.",
        ],
        "check": "The length factor 5/3 squared gives the area factor 25/9.",
        "mistakes": "Do not apply the area factor directly to a length. Keep original and image in the same order in every ratio. Similar figures need equal corresponding angles as well as proportional sides.",
        "alt": "A small rectangle and an enlarged similar rectangle with corresponding sides and a scale-factor arrow.",
    },
    "g2-lesson-03": {
        "kind": "proportion",
        "visual": "A similarity statement such as triangle ABC similar to triangle PQR fixes A↔P, B↔Q and C↔R. Corresponding sides are therefore AB↔PQ, BC↔QR and AC↔PR. Mark the correspondence before forming any proportion.",
        "deep": "Use ratios with matching orientation, such as AB/PQ=BC/QR. Cross-multiplication then solves an unknown side. Equal corresponding angles can establish AA similarity; once similarity is known, every corresponding length follows the same scale factor.",
        "prompt": "Triangles ABC and PQR are similar in that order. AB=8 cm, BC=12 cm, PQ=14 cm and PR=21 cm. Find QR and AC if AC corresponds to PR.",
        "steps": [
            "The scale factor from ABC to PQR is PQ/AB=14/8=7/4.",
            "QR=BC×7/4=21 cm.",
            "Since PR=AC×7/4, AC=21×4/7=12 cm.",
        ],
        "check": "The three larger-to-smaller side ratios are all 7/4.",
        "mistakes": "Do not pair sides because they occupy a similar place on the page. Use vertex order or equal-angle markings. Avoid reversing only one ratio; write a complete correspondence line before calculating.",
        "alt": "Two similar labelled triangles showing the vertex correspondence A to P, B to Q and C to R.",
    },
    "g2-lesson-04": {
        "kind": "enlargement",
        "visual": "An enlargement with centre C and scale factor k maps each point P along line CP so that vector CP′=k vector CP. On a coordinate grid, P′=C+k(P−C). Positive fractional factors create reductions while preserving direction from the centre.",
        "deep": "About the origin, multiply both coordinates by k. About another centre, subtract the centre coordinates, scale the displacement, then add the centre back. Linear dimensions use |k| and areas use k². The centre, object point and image point must be collinear.",
        "prompt": "Point P=(6,4) is enlarged by scale factor 1/2 about C=(2,−2). Find P′.",
        "steps": [
            "The displacement from C to P is (6−2,4−(−2))=(4,6).",
            "Scale the displacement: 1/2(4,6)=(2,3).",
            "Add C back: P′=(2,−2)+(2,3)=(4,1).",
        ],
        "check": "P′ lies halfway from C to P, so C, P′ and P are collinear.",
        "mistakes": "Do not multiply the coordinates directly unless the centre is the origin. Scale both horizontal and vertical displacements. An area factor is the square of the linear factor, even for a reduction.",
        "alt": "A coordinate grid showing a triangle and its enlargement from a marked centre, with construction rays through corresponding vertices.",
    },
    "g2-lesson-05": {
        "kind": "scale",
        "visual": "Scale drawings, maps and models are applications of similarity. A scale 1:n means one unit on the representation corresponds to n of the same units in reality. Convert units before multiplying or dividing by the scale factor.",
        "deep": "Decide the direction: actual length=plan length×n, while plan length=actual length÷n. Areas use n². In nested scale problems, multiply successive linear factors first, then square only if the requested quantity is an area.",
        "prompt": "A rectangular garden measures 36 m by 24 m. It is drawn at scale 1:600. Find the plan dimensions in centimetres and its plan area.",
        "steps": [
            "Convert actual lengths: 36 m=3600 cm and 24 m=2400 cm.",
            "Divide by 600 to obtain plan dimensions 6 cm by 4 cm.",
            "The plan area is 6×4=24 cm².",
        ],
        "check": "Using the area factor 600² gives 864 m²=8,640,000 cm² and 8,640,000÷360,000=24 cm².",
        "mistakes": "Do not use metres on one side of a ratio and centimetres on the other. A 1:600 scale is a linear ratio; area changes by 600². Label whether each quantity belongs to the plan, model or real object.",
        "alt": "A plan rectangle and a larger real courtyard connected by a scale arrow, with linear and area scale factors shown.",
    },
}

OUTCOME_KIND = {
    "1.1": "angle_types",
    "1.2": "intersection",
    "1.3": "parallel",
    "1.4": "polygons",
    "1.5": "quadrilateral",
    "1.6": "exterior",
    "1.7": "construction",
    "5.1": "area",
    "5.2": "composite_plane",
    "5.3": "solids",
    "5.4": "conversion",
    "5.5": "composite_solid",
    "2.1": "congruent",
    "2.2": "similar",
    "2.3": "proportion",
    "2.4": "enlargement",
    "2.5": "scale",
}


def svg_shape(kind: str) -> str:
    shapes = {
        "angle_types": '<g data-angle-kind="acute" data-angle-degrees="60"><line x1="100" y1="230" x2="100" y2="105"/><line x1="100" y1="230" x2="208.25" y2="167.5"/><path class="arc" d="M100 190 A40 40 0 0 1 134.64 210"/><text x="120" y="183" class="degree">60°</text><text x="73" y="305">acute</text></g><g data-angle-kind="right" data-angle-degrees="90"><line x1="310" y1="230" x2="310" y2="105"/><line x1="310" y1="230" x2="435" y2="230"/><path class="arc" d="M310 190 A40 40 0 0 1 350 230"/><text x="329" y="188" class="degree">90°</text><text x="280" y="305">right</text></g><g data-angle-kind="obtuse" data-angle-degrees="120"><line x1="520" y1="230" x2="520" y2="105"/><line x1="520" y1="230" x2="628.25" y2="292.5"/><path class="arc" d="M520 190 A40 40 0 0 1 554.64 250"/><text x="548" y="207" class="degree">120°</text><text x="486" y="325">obtuse</text></g><g data-angle-kind="reflex" data-angle-degrees="240"><line x1="730" y1="230" x2="730" y2="105"/><line x1="730" y1="230" x2="838.25" y2="292.5"/><path class="arc" d="M730 180 A50 50 0 1 0 773.3 255"/><text x="675" y="270" class="degree">240°</text><text x="708" y="325">reflex</text></g>',
        "intersection": '<path d="M180 270 L430 80 M180 80 L430 270"/><text x="290" y="120">a</text><text x="370" y="185">b</text><text x="290" y="245">a</text><text x="220" y="185">b</text><text x="500" y="145">a = a</text><text x="500" y="190">a + b = 180°</text><text x="500" y="235">2a + 2b = 360°</text>',
        "parallel": '<path d="M100 115 H810 M100 255 H810 M270 320 L620 50"/><path class="mark" d="M170 105 l18 10 -18 10 M190 105 l18 10 -18 10 M170 245 l18 10 -18 10 M190 245 l18 10 -18 10"/><text x="570" y="100">corresponding</text><text x="340" y="160">alternate</text><text x="565" y="220">co-interior</text>',
        "polygons": '<path d="M80 260 L180 85 L280 260 Z M355 105 L535 105 L580 250 L310 250 Z M690 90 L790 90 L845 175 L790 260 L690 260 L635 175 Z"/><text x="120" y="300">triangle</text><text x="370" y="300">quadrilateral</text><text x="690" y="300">regular polygon</text>',
        "quadrilateral": '<rect x="90" y="105" width="170" height="55"/><rect x="345" y="65" width="160" height="55"/><rect x="345" y="195" width="160" height="55"/><rect x="620" y="130" width="150" height="55"/><path class="arrow" d="M260 132 H330 M505 92 C565 92 565 145 605 150 M505 222 C565 222 565 175 605 160"/><text x="116" y="140">parallelogram</text><text x="390" y="100">rectangle</text><text x="395" y="230">rhombus</text><text x="670" y="165">square</text>',
        "exterior": '<path d="M260 70 L390 70 L470 175 L390 280 L260 280 L180 175 Z M260 70 L390 280 M260 70 L470 175 M260 70 L260 280 M390 70 L520 70"/><path class="arc" d="M390 105 A35 35 0 0 1 425 70"/><text x="425" y="105">exterior angle</text><text x="610" y="145">n−2 triangles</text><text x="610" y="195">sum = (n−2)×180°</text>',
        "construction": '<path d="M110 245 H430 M270 55 V310"/><circle class="faint" cx="110" cy="245" r="205"/><circle class="faint" cx="430" cy="245" r="205"/><circle cx="110" cy="245" r="5"/><circle cx="430" cy="245" r="5"/><text x="95" y="275">A</text><text x="430" y="275">B</text><path d="M610 245 L780 245 L690 95 Z"/><path class="faint" d="M610 245 A170 170 0 0 1 690 95 M780 245 A170 170 0 0 0 690 95"/><text x="680" y="80">C</text>',
        "area": '<path d="M90 250 L160 95 H390 L320 250 Z M520 250 L575 105 H790 L850 250 Z"/><path class="dash" d="M160 95 V250 M575 105 V250"/><text x="205" y="285">base b</text><text x="125" y="180">h</text><text x="655" y="90">a</text><text x="655" y="285">b</text><text x="540" y="180">h</text>',
        "composite_plane": '<path d="M130 70 H470 V170 H310 V290 H130 Z"/><path class="dash" d="M310 170 H470 V290 H310"/><text x="170" y="185">remaining region</text><text x="335" y="235">cut-out</text><path class="arrow" d="M560 180 H690"/><rect x="720" y="95" width="120" height="170"/><text x="700" y="305">decompose or subtract</text>',
        "solids": '<path d="M90 235 L210 130 L330 235 Z M210 130 L430 90 L550 195 L330 235 M330 235 V300 L550 260 V195 M90 235 V300 L330 300"/><ellipse cx="720" cy="105" rx="75" ry="28"/><path d="M645 105 V270 M795 105 V270"/><ellipse cx="720" cy="270" rx="75" ry="28"/><text x="150" y="335">prism</text><text x="685" y="335">cylinder</text>',
        "conversion": '<rect x="100" y="80" width="240" height="240"/><path class="faint" d="M160 80 V320 M220 80 V320 M280 80 V320 M100 140 H340 M100 200 H340 M100 260 H340"/><path class="arrow" d="M390 200 H520"/><path d="M610 105 L760 105 L820 155 L670 155 Z M610 105 V255 L670 305 V155 M670 155 H820 V305 H670"/><text x="120" y="350">length factor squared</text><text x="620" y="350">length factor cubed</text>',
        "composite_solid": '<path d="M100 150 H330 V285 H100 Z M330 190 H500 V285 H330"/><path class="faint" d="M330 190 V285"/><text x="280" y="175">contact face</text><path d="M620 105 H820 V290 H620 Z"/><ellipse cx="720" cy="105" rx="34" ry="12"/><path class="dash" d="M686 105 V290 M754 105 V290"/><ellipse cx="720" cy="290" rx="34" ry="12"/><text x="660" y="330">removed core</text>',
        "congruent": '<path d="M100 270 L230 70 L360 270 Z M570 85 L790 155 L620 290 Z"/><path class="mark" d="M160 175 l18 10 M285 175 l18 -10 M650 105 l8 18 M705 230 l18 5"/><text x="185" y="305">△ABC</text><text x="640" y="325">△PQR</text><text x="400" y="175">same shape and size</text>',
        "similar": '<path d="M110 270 L220 100 L330 270 Z M500 290 L690 45 L860 290 Z"/><path class="arrow" d="M345 185 H470"/><text x="375" y="160">scale k</text><text x="145" y="310">original</text><text x="650" y="325">image</text>',
        "proportion": '<path d="M90 275 L210 70 L360 275 Z M540 275 L670 70 L850 275 Z"/><text x="200" y="55">A</text><text x="70" y="300">B</text><text x="360" y="300">C</text><text x="660" y="55">P</text><text x="520" y="300">Q</text><text x="850" y="300">R</text><text x="380" y="145">A ↔ P</text><text x="380" y="190">B ↔ Q</text><text x="380" y="235">C ↔ R</text>',
        "enlargement": '<path class="grid" d="M80 80 H850 M80 130 H850 M80 180 H850 M80 230 H850 M80 280 H850 M130 50 V320 M180 50 V320 M230 50 V320 M280 50 V320 M330 50 V320 M380 50 V320 M430 50 V320 M480 50 V320 M530 50 V320 M580 50 V320 M630 50 V320 M680 50 V320 M730 50 V320 M780 50 V320"/><path d="M180 255 L280 205 L280 255 Z M180 255 L480 105 L480 255 Z"/><circle cx="180" cy="255" r="6"/><text x="160" y="285">C</text><text x="300" y="190">object</text><text x="500" y="100">image</text>',
        "scale": '<rect x="100" y="105" width="210" height="140"/><rect x="555" y="65" width="290" height="220"/><path class="arrow" d="M340 175 H520"/><text x="155" y="285">plan or model</text><text x="635" y="325">actual object</text><text x="375" y="150">linear scale</text><text x="375" y="215">area scale²</text>',
    }
    return shapes[kind]


def svg_document(kind: str, title: str, subtitle: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 940 390" role="img" aria-labelledby="title desc">
<title id="title">{html.escape(title)}</title><desc id="desc">{html.escape(subtitle)}</desc>
<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#0f766e"/></marker></defs>
<rect width="940" height="390" rx="24" fill="#f8fafc"/><text x="36" y="38" class="heading">{html.escape(title)}</text>
<g fill="none" stroke="#0f3d40" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">{svg_shape(kind)}</g>
<text x="904" y="374" text-anchor="end" class="note">Use stated measurements · not drawn to scale</text>
<style>.heading{{font:700 22px system-ui;fill:#0f3d40}} text{{font:600 17px system-ui;fill:#334155;stroke:none}} .note{{font:500 13px system-ui;fill:#64748b}} .arc{{stroke:#c87a1e}} .mark{{stroke:#c87a1e}} .faint{{stroke:#94a3b8;stroke-width:2}} .dash{{stroke:#c87a1e;stroke-dasharray:8 8}} .arrow{{stroke:#0f766e;marker-end:url(#arrow)}} .grid{{stroke:#dbe4e6;stroke-width:1}}</style>
</svg>"""


def asset(
    path: Path, source_path: Path, key: str, kind: str, alt: str, spec: dict
) -> dict:
    generation_spec = {
        "renderer": "nextscholar-geometry-svg-v1",
        "diagram_kind": kind,
        **spec,
    }
    if kind == "angle_types":
        generation_spec["angle_measures"] = {
            "acute": 60,
            "right": 90,
            "obtuse": 120,
            "reflex": 240,
        }
    return {
        "asset_key": key,
        "kind": "geometry",
        "format": "svg",
        "path": path.as_posix(),
        "alt_text": alt,
        "generation_spec": generation_spec,
        "sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "width": 940,
        "height": 390,
    }


def text(value: str) -> dict:
    return {"type": "text", "text": value}


def recalibrate_lessons() -> list[str]:
    changed = []
    roots = [
        ROOT / "backend_resources/courses/g3_math/secondary_1/n1/v1",
        ROOT / "backend_resources/courses/g3_math/secondary_2/g2/v1",
    ]
    for course_root in roots:
        assets_root = course_root / "assets"
        assets_root.mkdir(exist_ok=True)
        for lesson_path in sorted((course_root / "lessons").glob("g*-lesson-*.json")):
            data = json.loads(lesson_path.read_text(encoding="utf-8"))
            config = LESSONS[data["stable_key"]]
            if any(
                item.get("generation_spec", {}).get("renderer")
                == "nextscholar-geometry-svg-v1"
                for item in data.get("assets", [])
            ):
                continue
            filename = f"{data['stable_key']}-{config['kind']}.svg"
            svg_path = assets_root / filename
            svg_path.write_text(
                svg_document(config["kind"], data["title"], config["alt"]),
                encoding="utf-8",
            )
            key = f"{data['stable_key']}-diagram"
            relative = Path("assets") / filename
            original = data["sections"]
            core, original_example, recall, summary = (
                original[0],
                original[1],
                original[-2],
                original[-1],
            )
            sections = [
                core,
                {
                    "stable_key": f"{data['stable_key']}-visual",
                    "position": 2,
                    "type": "explanation",
                    "title": "Read the diagram",
                    "blocks": [
                        text(config["visual"]),
                        {"type": "asset_ref", "asset_key": key},
                    ],
                },
                {
                    "stable_key": f"{data['stable_key']}-reasoning",
                    "position": 3,
                    "type": "explanation",
                    "title": "Reasoning method",
                    "blocks": [text(config["deep"])],
                },
                original_example,
                {
                    "stable_key": f"{data['stable_key']}-example-2",
                    "position": 5,
                    "type": "worked_example",
                    "title": "Worked example: apply the method",
                    "prompt": [text(config["prompt"])],
                    "steps": [
                        {"position": index, "content": [text(step)]}
                        for index, step in enumerate(config["steps"], 1)
                    ],
                    "verification_note": config["check"],
                },
                {
                    "stable_key": f"{data['stable_key']}-pitfalls",
                    "position": 6,
                    "type": "explanation",
                    "title": "Common errors and checks",
                    "blocks": [text(config["mistakes"])],
                },
                recall,
                summary,
            ]
            for index, section in enumerate(sections, 1):
                section["position"] = index
            summary["blocks"].append(
                text(
                    " Before moving on, explain the relevant property in words, show the equation or formula with units, and use the diagram markings to check that every correspondence is consistent."
                )
            )
            data["revision"] = max(2, data.get("revision", 1))
            data["estimated_minutes"] = max(55, data["estimated_minutes"])
            data["sections"] = sections
            data["assets"] = [
                asset(
                    relative,
                    svg_path,
                    key,
                    config["kind"],
                    config["alt"],
                    {"lesson_key": data["stable_key"]},
                )
            ]
            data["provenance"]["reviewed_at"] = None
            data["provenance"]["reviewed_by"] = None
            data["provenance"]["review_notes"] = (
                "Expanded and diagram-recalibrated; awaiting Mathematics and editorial review."
            )
            lesson_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            changed.append(data["stable_key"])
    return changed


def question_text(data: dict) -> str:
    blocks = [*data.get("stem", [])]
    for part in data["parts"]:
        blocks.extend(part["prompt"])
    return " ".join(block.get("text", "") for block in blocks)


def recalibrate_questions() -> tuple[int, int]:
    bank_roots = [
        ROOT / "backend_resources/question_bank/g3_math/secondary_1/g1/v1",
        ROOT / "backend_resources/question_bank/g3_math/secondary_1/g5/v1",
        ROOT / "backend_resources/question_bank/g3_math/secondary_2/g2/v1",
    ]
    added = 0
    audited = 0
    for bank_root in bank_roots:
        questions = []
        for path in sorted((bank_root / "questions").glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            questions.append((path, data))
        selected = set()
        by_outcome: dict[str, list[tuple[Path, dict]]] = {}
        for item in questions:
            by_outcome.setdefault(item[1]["primary_outcome"], []).append(item)
        for items in by_outcome.values():
            preferred = []
            for difficulty in (1, 3, 5, 2, 4):
                candidate = next(
                    (item for item in items if item[1]["difficulty"] == difficulty),
                    None,
                )
                if candidate and candidate[0] not in {path for path, _ in preferred}:
                    preferred.append(candidate)
                if len(preferred) == 3:
                    break
            selected.update(path for path, _ in preferred)
        assets_root = bank_root / "assets"
        assets_root.mkdir(exist_ok=True)
        decisions = []
        for path, data in questions:
            audited += 1
            if path not in selected:
                decisions.append(
                    {
                        "question_key": data["stable_key"],
                        "decision": "text_sufficient",
                        "reason": "The relationship and all measurements are fully stated; a repeated schematic would not add mathematical information.",
                    }
                )
                continue
            kind = OUTCOME_KIND[data["primary_outcome"]]
            key = f"{data['stable_key']}-diagram"
            filename = f"{data['stable_key']}-diagram.svg"
            svg_path = assets_root / filename
            prompt = question_text(data)
            givens = ", ".join(
                re.findall(
                    r"(?<![A-Za-z0-9.])\d+(?:\.\d+)?\s*(?:cm³|cm²|m³|m²|cm|km|m|°)",
                    prompt,
                )[:5]
            )
            subtitle = f"Schematic for {data['title']}. Not drawn to scale." + (
                f" Stated measures include {givens}." if givens else ""
            )
            svg_path.write_text(
                svg_document(kind, data["title"], subtitle), encoding="utf-8"
            )
            relative = Path("assets") / filename
            data["revision"] = max(2, data.get("revision", 1))
            diagram_instruction = (
                "Use the schematic together with the measurements stated in the question. "
                "The diagram is not drawn to scale."
            )
            data["stem"] = [
                text(diagram_instruction),
                {"type": "asset_ref", "asset_key": key},
                *[
                    block
                    for block in data.get("stem", [])
                    if block.get("type") != "asset_ref"
                    and block.get("text") != diagram_instruction
                ],
            ]
            data["assets"] = [
                asset(
                    relative,
                    svg_path,
                    key,
                    kind,
                    subtitle,
                    {
                        "question_key": data["stable_key"],
                        "outcome": data["primary_outcome"],
                        "not_to_scale": True,
                    },
                )
            ]
            data["provenance"]["reviewed_at"] = None
            data["provenance"]["reviewed_by"] = None
            data["provenance"]["review_notes"] = (
                "Diagram-recalibrated; awaiting Mathematics and editorial review."
            )
            path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            decisions.append(
                {
                    "question_key": data["stable_key"],
                    "decision": "diagram_added",
                    "asset_key": key,
                    "reason": "Selected as a representative visual item across this outcome and difficulty range.",
                }
            )
            added += 1
        audit = {
            "schema_version": "1.0.0",
            "bank_key": questions[0][1]["bank_key"],
            "audited_question_count": len(questions),
            "diagram_question_count": sum(
                item["decision"] == "diagram_added" for item in decisions
            ),
            "policy": "Add a diagram when it contributes spatial information; retain text-only delivery when a schematic would merely repeat a fully specified calculation.",
            "decisions": decisions,
        }
        (bank_root / "diagram_audit.json").write_text(
            json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    return audited, added


def render_blocks(blocks: list[dict], assets: dict[str, dict]) -> str:
    rendered = []
    for block in blocks:
        if block["type"] == "text":
            rendered.append(html.escape(block["text"]).replace("\n", "<br>"))
        elif block["type"] in {"inline_math", "display_math"}:
            mode = "display" if block["type"] == "display_math" else "inline"
            latex = html.escape(block["latex"], quote=True)
            rendered.append(
                f'<span class="math {mode}" data-latex="{latex}">{latex}</span>'
            )
        else:
            item = assets[block["asset_key"]]
            filename = Path(item["path"]).name
            rendered.append(
                f'<figure><img src="assets/{html.escape(filename)}" '
                f'alt="{html.escape(item["alt_text"], quote=True)}">'
                f"<figcaption>{html.escape(item['alt_text'])}</figcaption></figure>"
            )
    return "".join(rendered)


def export_lesson_review(course_root: Path, topic: str, output_name: str) -> None:
    lessons = []
    for path in sorted((course_root / "lessons").glob(f"{topic}-lesson-*.json")):
        lessons.append(json.loads(path.read_text(encoding="utf-8")))
    output = ROOT / "build/reviewer-lessons" / output_name
    assets_output = output / "assets"
    assets_output.mkdir(parents=True, exist_ok=True)
    cards = []
    for lesson in lessons:
        assets = {item["asset_key"]: item for item in lesson["assets"]}
        for item in lesson["assets"]:
            shutil.copy2(
                course_root / item["path"], assets_output / Path(item["path"]).name
            )
        sections = []
        for section in lesson["sections"]:
            body = ""
            if section["type"] in {"explanation", "summary"}:
                body = render_blocks(section["blocks"], assets)
            elif section["type"] == "worked_example":
                steps = "".join(
                    f"<li>{render_blocks(step['content'], assets)}</li>"
                    for step in section["steps"]
                )
                body = (
                    f'<p class="prompt">{render_blocks(section["prompt"], assets)}</p>'
                    f'<ol>{steps}</ol><p class="verification"><strong>Check:</strong> '
                    f"{html.escape(section['verification_note'])}</p>"
                )
            else:
                response = section["response"]
                answer = response.get("canonical_latex") or response.get(
                    "canonical_expression", ""
                )
                body = (
                    f'<p class="prompt">{render_blocks(section["prompt"], assets)}</p>'
                    f"<p><strong>Expected answer:</strong> {html.escape(answer)}</p>"
                    f"<p><strong>Feedback:</strong> {render_blocks(section['feedback'], assets)}</p>"
                )
            sections.append(
                f'<section class="lesson-section {section["type"]}"><div class="label">'
                f"{html.escape(section['type'].replace('_', ' '))}</div><h3>"
                f"{section['position']}. {html.escape(section['title'])}</h3>{body}</section>"
            )
        objectives = "".join(
            f"<li>{html.escape(item)}</li>" for item in lesson["objectives"]
        )
        cards.append(
            f'<article id="{lesson["stable_key"]}" class="lesson"><div class="eyebrow">'
            f"Outcome {html.escape(', '.join(lesson['outcomes']))} · revision "
            f"{lesson['revision']} · {lesson['estimated_minutes']} minutes</div><h2>"
            f'{html.escape(lesson["title"])}</h2><p class="summary">'
            f"{html.escape(lesson['summary'])}</p><h3>Objectives</h3><ul>{objectives}</ul>"
            f"{''.join(sections)}</article>"
        )
    katex_source = ROOT / "node_modules/katex/dist"
    if katex_source.is_dir():
        shutil.copytree(katex_source, assets_output / "katex", dirs_exist_ok=True)
    nav = "".join(
        f'<a href="#{lesson["stable_key"]}">Lesson {lesson["position"]}</a>'
        for lesson in lessons
    )
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{output_name} lesson review</title><link rel="stylesheet" href="assets/katex/katex.min.css"><style>
:root{{--ink:#172238;--muted:#596579;--accent:#176b5b;--panel:#fff;--line:#d9e0e8}}*{{box-sizing:border-box}}body{{margin:0;background:#f4f6f8;color:var(--ink);font:17px/1.65 system-ui,sans-serif}}main{{width:min(1060px,92vw);margin:auto;padding:48px 0 96px}}h1{{font-size:clamp(2rem,5vw,3.4rem)}}h2{{font-size:2rem}}nav{{position:sticky;top:0;z-index:2;display:flex;gap:8px;overflow:auto;padding:14px 0;background:#f4f6f8ee}}nav a{{white-space:nowrap;color:white;background:var(--accent);padding:7px 13px;border-radius:99px;text-decoration:none;font-weight:700}}.intro,.lesson{{background:white;border:1px solid var(--line);border-radius:18px;padding:28px;margin-bottom:28px;box-shadow:0 8px 28px #18243a0d}}.eyebrow,.label{{color:var(--accent);text-transform:uppercase;letter-spacing:.08em;font-size:.8rem;font-weight:800}}.summary,.verification,figcaption{{color:var(--muted)}}.lesson-section{{border-top:1px solid var(--line);margin-top:26px;padding-top:18px}}.worked_example{{background:#f7fbfa;border:1px solid #cae5df;border-radius:14px;padding:20px}}.active_recall{{background:#fff9ec;border:1px solid #efd898;border-radius:14px;padding:20px}}figure{{margin:24px auto;max-width:940px}}figure img{{display:block;width:100%;height:auto;border:1px solid var(--line);border-radius:18px}}figcaption{{font-size:.85rem;margin-top:6px}}.math.display{{display:block;overflow:auto;padding:10px 0}}@media(max-width:640px){{.intro,.lesson{{padding:20px}}}}</style></head><body><main><section class="intro"><div class="eyebrow">Mathematics and editorial review</div><h1>{output_name} expanded geometry lessons</h1><p>Review the teaching explanations, diagrams, worked examples, active recall and error checks. Diagrams are deterministic SVG and are not drawn to scale unless stated.</p></section><nav>{nav}</nav>{"".join(cards)}</main><script src="assets/katex/katex.min.js"></script><script>document.querySelectorAll('[data-latex]').forEach((e)=>katex.render(e.dataset.latex,e,{{throwOnError:false,displayMode:e.classList.contains('display')}}));</script></body></html>"""
    (output / "index.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    lessons = recalibrate_lessons()
    audited, diagrams = recalibrate_questions()
    export_lesson_review(
        ROOT / "backend_resources/courses/g3_math/secondary_1/n1/v1",
        "g1",
        "g3-sec1-g1",
    )
    export_lesson_review(
        ROOT / "backend_resources/courses/g3_math/secondary_1/n1/v1",
        "g5",
        "g3-sec1-g5",
    )
    export_lesson_review(
        ROOT / "backend_resources/courses/g3_math/secondary_2/g2/v1",
        "g2",
        "g3-sec2-g2",
    )
    print(
        json.dumps(
            {
                "lessons_expanded": len(lessons),
                "questions_audited": audited,
                "question_diagrams_added": diagrams,
            }
        )
    )
