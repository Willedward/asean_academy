# Answer-checker form settings for content PRs

This list supports the answer-checker fix on `fix/answer-checker`. That PR changes code only. It does
not edit question or lesson content, so the settings below are applied by the content PRs. The list was
generated from every `symbolic_equivalence` part in all question banks (`backend_resources/question_bank`)
and all lesson active-recall checks (`backend_resources/courses`): 194 bank parts and 15 lesson checks, 209 in all.

## How to apply a form

Set `checker_config` on the part's `response` (or the lesson section's `response`):

```json
"checker_config": {"form": "expanded"}
```

An empty `checker_config` means `"form": "any"`, which is the old behaviour: every equivalent
expression is accepted. The response model rejects unknown forms, unknown `checker_config` keys on
`symbolic_equivalence`, and a `form` on any other comparison mode. Changed content needs an incremented
`revision`. After applying a form, `question-bank authoring-validate` and
`tests/test_checking.py::test_every_authored_canonical_and_accepted_answer_passes` confirm that the
canonical answer satisfies its own form.

| Form | Accepted written form | Typical prompt |
| --- | --- | --- |
| `any` | Any equivalent expression | Word problems, nth term, make x the subject |
| `expanded` | A sum of terms, like terms collected, no brackets, one coefficient per term, each letter once per term (`6x^2+7x-20`, `a^2b`, `5x/4-2`) | Expand; simplify to a polynomial; write in index notation; write as a product |
| `factorised` | A product of at least two factors, at least one a bracketed sum with like terms collected | Factorise (when a partial factorisation is acceptable) |
| `factorised_completely` | Factorised; every bracket has integer coefficients with no common factor and no common letter; no one-letter quadratic bracket with a rational root; no fewer non-constant factors than the canonical | Factorise, factorise completely, take out the greatest common factor |
| `simplified_fraction` | Expanded, factorised, or one fraction N/D in lowest terms (integer coefficients with no common factor, and no common polynomial factor) | Simplify an algebraic fraction or a sum of fractions |

With any form other than `any`, retyping the expression from the prompt (for example `3(x+4)` for
"Simplify 3(x+4)", or `x^2+10x+24` for "Factorise x^2+10x+24") is marked incorrect. That was
checked for all 124 parts whose prompt states the original expression.

## Summary

- 135 parts need a form: 61 `expanded`, 38 `factorised_completely`, 36 `simplified_fraction`.
- 1 part asks for a form that no checker setting expresses (repeated addition, see below).
- 73 parts need no form: word problems, nth-term rules, "write as one expression" and "make x the subject" tasks.
- 11 canonical answers are not complete factorisations. Their canonical, `canonical_latex` and final solution step must change in the same content PR that sets the form (audit finding C-2 in `PRE_REVIEW_AUDIT_secondary_2_n5.md`, plus `n5-l3-008`).

## Parts that need a form

Rows marked *judgement* follow the recommended reading of the prompt but are a reviewer decision.

| File | Part | Task | Canonical | Form | Note |
| --- | --- | --- | --- | --- | --- |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l1-005.json` | 1 | Expand 5(x + 2). | `5x+10` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l1-007.json` | 1 | Write a × a × b using index notation. | `a^2b` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l1-010.json` | 1 | Simplify 3x + 5x. | `8x` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l1-012.json` | 1 | Write y + y + y + y as a product. | `4y` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l1-015.json` | 1 | Simplify 9y - 4y. | `5y` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l1-016.json` | 1 | Simplify 3(x + 4). | `3x+12` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l1-020.json` | 1 | Simplify -2(y - 5). | `-2y+10` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l1-021.json` | 1 | Factorise 6x + 12 by extracting the greatest common factor. | `6(x+2)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l2-006.json` | 1 | Simplify (3x + 7) + (5x - 2). | `8x+5` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l2-007.json` | 1 | Simplify 4(x + 3) + 2x. | `6x+12` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l2-008.json` | 1 | Expand 4(3a - 5). | `12a-20` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l2-010.json` | 1 | Write x × x × x × y × y in index notation. | `x^3y^2` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l2-012.json` | 1 | A rectangular garden has length (x + 3) metres and width x metres. Write its perimeter … | `4x+6` | `expanded` | *judgement*: should a factorised answer also pass? |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l2-014.json` | 1 | Simplify (8a - 3) - (2a + 5). | `6a-8` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l2-015.json` | 1 | Simplify 7a - 3(2a - 4). | `a+12` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l2-016.json` | 1 | Factorise 15y - 20 completely. | `5(3y-4)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l2-021.json` | 1 | Simplify 4p + 3q - p + 2q. | `3p+5q` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l2-022.json` | 1 | Simplify 2(p + 5) + 3(p - 1). | `5p+7` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l2-023.json` | 1 | Factorise 8m² + 12m completely. | `4m(2m+3)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l2-029.json` | 1 | Simplify (-2m + 6) + (5m - 9). | `3m-3` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l2-030.json` | 1 | Simplify (1/2)(6m - 8) + m. | `4m-4` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l2-031.json` | 1 | Expand -3(2p - 7). | `-6p+21` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l3-001.json` | 1 | The smallest of three consecutive even integers is 2n. Write their sum in simplest form. | `6n+6` | `expanded` | *judgement*: should a factorised answer also pass? |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l3-006.json` | 1 | Simplify (7x + 2y - 4) - (3x - 5y + 6). | `4x+7y-10` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l3-007.json` | 1 | Simplify 3[2x - (x - 4)]. | `3x+12` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l3-008.json` | 1 | Factorise 12x² - 18x + 6 completely. | `6(2x^2-3x+1)` | `factorised_completely` | Canonical is not complete; use `6*(2*x-1)*(x-1)` |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l3-010.json` | 1 | Write the square of the product 2xy using index notation and simplify the numerical fac… | `4x^2y^2` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l3-013.json` | 1 | Simplify (2a - b + 3) + (5a + 4b - 8) - (a + b - 2). | `6a+2b-3` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l3-014.json` | 1 | Simplify 5(2a - 3) - 2(3a + 4). | `4a-23` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l3-015.json` | 1 | Expand and simplify 3(2a - 5) - 2(a + 4). | `4a-23` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l3-021.json` | 1 | Simplify (x/2 + 3) + (3x/4 - 5). | `5x/4-2` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l3-022.json` | 1 | Simplify [2x - 3(x - 5)]/3. | `(15-x)/3` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l3-023.json` | 1 | Factorise 14ab + 21a completely. | `7a(2b+3)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l3-029.json` | 1 | Simplify (5y/6 - 2) - (y/3 + 4). | `y/2-6` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l3-030.json` | 1 | Simplify -2(3x - 5y) + 4(x + y). | `-2x+14y` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l3-031.json` | 1 | Simplify 5x + 10y - 2x - 4y, then factorise completely. | `3(x+2y)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l4-003.json` | 1 | Simplify 2(3x - y + 4) - [x + 3(y - 2)]. | `5x-5y+14` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l4-004.json` | 1 | Simplify [3(2x - 1) - 2(x + 4)]/5 + x. | `(9x-11)/5` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l4-007.json` | 1 | Plan A charges $18 plus $0.08 per message. Plan B charges $25 plus $0.03 per message. W… | `0.05m-7` | `expanded` | *judgement*: should a factorised answer also pass? |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l4-008.json` | 1 | Simplify 2{3a - [2b - (a - b)]} - 5a. | `3a-6b` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l4-009.json` | 1 | Factorise 6ax - 9ay + 4bx - 6by completely. | `(3a+2b)(2x-3y)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l4-011.json` | 1 | A photograph is x cm wide and y cm high. A frame extends 3 cm beyond every edge. Write … | `6x+6y+36` | `expanded` | *judgement*: should a factorised answer also pass? |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l4-013.json` | 1 | Expand and simplify 2[3x - 4(1 - x)] - 5x. | `9x-8` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l4-014.json` | 1 | A two-digit number has tens digit a and units digit b. Write the original number minus … | `9a-9b` | `expanded` | *judgement*: should a factorised answer also pass? |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l4-016.json` | 1 | Simplify (2x - y)/3 - (x + 2y)/6. | `(3x-4y)/6` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l5-001.json` | 1 | Pattern A has nth term 5n - 2. Pattern B has 11 objects at stage 2 and 23 objects at st… | `9n+1` | `expanded` | *judgement*: should a factorised answer also pass? |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l5-002.json` | 1 | Simplify 3{2x - [y - (x - 2y)]} - 2(x + y). | `7x-11y` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l5-003.json` | 1 | Simplify [2{3x - (2y - x)} - (x + y)]/3 - x. | `(4x-5y)/3` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l5-005.json` | 1 | Factorise 12ax - 8ay - 9bx + 6by completely. | `(4a-3b)(3x-2y)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_1/n5/v2/questions/n5-l3-901.json` | 1 | Write the product of the smallest and largest integers as an expression in n, in simple… | `4*n^2+12*n+5` | `expanded` | *judgement*: should a factorised answer also pass? |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l1-502.json` | 1 | Expand and simplify (x+3)². | `x^2+6x+9` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l1-503.json` | 1 | Factorise ax+bx+3ay+3by completely. | `(a+b)*(x+3*y)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l1-504.json` | 1 | Simplify 2/(x-3)+4/(x-3). | `6/(x-3)` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l1-505.json` | 1 | Expand and simplify 3(x+2). | `3*x+6` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l1-507.json` | 1 | Expand and simplify (x+6)². | `x^2+12x+36` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l1-508.json` | 1 | Factorise 3p-3q+4px-4qx completely. | `(p-q)*(3+4*x)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l1-509.json` | 1 | Factorise x^2+10x+24. | `(x+6)*(x+4)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l1-510.json` | 1 | Expand and simplify 3(x+1). | `3*x+3` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l1-513.json` | 1 | Factorise 2p-2q+7px-7qx completely. | `(p-q)*(2+7*x)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l1-514.json` | 1 | Factorise x^2+9x+20. | `(x+4)*(x+5)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l1-515.json` | 1 | Simplify (5a/5b)(6b²/9a²). | `(2*b)/(3*a)` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l1-516.json` | 1 | Expand and simplify 2(x+4). | `2*x+8` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l1-519.json` | 1 | Expand and simplify (x+5)². | `x^2+10x+25` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l1-520.json` | 1 | Simplify (5a/4b)(4b²/8a²). | `(5*b)/(8*a)` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l1-521.json` | 1 | Simplify 3/(x-2)+3/(x-2). | `6/(x-2)` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-503.json` | 1 | Expand and simplify (4x-3)². | `16x^2-24x+9` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-504.json` | 1 | Factorise 4p-4q+6px-6qx completely. | `(p-q)*(4+6*x)` | `factorised_completely` | Canonical is not complete; use `2*(p-q)*(2+3*x)` |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-505.json` | 1 | Factorise x^2-8x+15. | `(x-3)*(x-5)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-506.json` | 1 | Simplify (3x/4y)÷(6x²/8y²). | `(y)/(x)` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-507.json` | 1 | Simplify 3/(x-4)+5/(x-7). | `(8*x-41)/((x-4)*(x-7))` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-508.json` | 1 | Expand and simplify (x+3)(x+6). | `x^2+9x+18` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-511.json` | 1 | Expand and simplify (3x-6)². | `9x^2-36x+36` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-512.json` | 1 | Factorise 4x+4y+5kx+5ky completely. | `(x+y)*(4+5*k)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-513.json` | 1 | Factorise x^2-13x+42. | `(x-7)*(x-6)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-514.json` | 1 | Simplify (2x/7y)÷(9x²/6y²). | `(4*y)/(21*x)` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-515.json` | 1 | Simplify 1/(x-6)+2/(x-8). | `(3*x-20)/((x-6)*(x-8))` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-516.json` | 1 | Expand and simplify (x+2)(x+5). | `x^2+7x+10` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-519.json` | 1 | Expand and simplify (5x-2)². | `25x^2-20x+4` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-520.json` | 1 | Factorise x^2-12x+35. | `(x-5)*(x-7)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-521.json` | 1 | Simplify (2x/6y)÷(7x²/5y²). | `(5*y)/(21*x)` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-522.json` | 1 | Simplify 4/(x-4)+5/(x-6). | `(9*x-44)/((x-4)*(x-6))` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-523.json` | 1 | Expand and simplify (x+5)(x+3). | `x^2+8x+15` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-526.json` | 1 | Expand and simplify (5x-6)². | `25x^2-60x+36` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-527.json` | 1 | Factorise 5p-5q+5px-5qx completely. | `(p-q)*(5+5*x)` | `factorised_completely` | Canonical is not complete; use `5*(p-q)*(1+x)` |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-528.json` | 1 | Factorise x^2-11x+28. | `(x-7)*(x-4)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-529.json` | 1 | Simplify (2x/5y)÷(5x²/9y²). | `(18*y)/(25*x)` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-530.json` | 1 | Simplify 4/(x-3)+4/(x-6). | `(8*x-36)/((x-3)*(x-6))` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l2-531.json` | 1 | Expand and simplify (x+2)(x+5). | `x^2+7x+10` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l3-504.json` | 1 | Factorise 5x+5y+7kx+7ky completely. | `(x+y)*(5+7*k)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l3-505.json` | 1 | Factorise 4x^2+32x+28. | `(4*x+4)*(1*x+7)` | `factorised_completely` | Canonical is not complete; use `4*(x+1)*(x+7)` |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l3-506.json` | 1 | Simplify ((x+4)/4x)(7x²/(x+4)). | `(7*x)/(4)` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l3-507.json` | 1 | Simplify 4/(x²-25)+6/(x-5). | `(6*x+34)/((x-5)*(x+5))` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l3-508.json` | 1 | Expand and simplify (5x+4)(2x-2). | `10x^2-2x-8` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l3-511.json` | 1 | Factorise ax+bx+4ay+4by completely. | `(a+b)*(x+4*y)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l3-512.json` | 1 | Factorise 4x^2+20x+16. | `(2*x+2)*(2*x+8)` | `factorised_completely` | Canonical is not complete; use `4*(x+1)*(x+4)` |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l3-513.json` | 1 | Simplify ((x+7)/3x)(5x²/(x+7)). | `(5*x)/(3)` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l3-514.json` | 1 | Simplify 2/(x²-4)+3/(x-2). | `(3*x+8)/((x-2)*(x+2))` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l3-515.json` | 1 | Expand and simplify (5x+3)(3x-6). | `15x^2-21x-18` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l3-519.json` | 1 | Factorise 3x+3y+3kx+3ky completely. | `(x+y)*(3+3*k)` | `factorised_completely` | Canonical is not complete; use `3*(x+y)*(1+k)` |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l3-520.json` | 1 | Factorise 9x^2+45x+54. | `(3*x+6)*(3*x+9)` | `factorised_completely` | Canonical is not complete; use `9*(x+2)*(x+3)` |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l3-521.json` | 1 | Simplify ((x+4)/3x)(4x²/(x+4)). | `(4*x)/(3)` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l3-522.json` | 1 | Simplify 1/(x²-25)+6/(x-5). | `(6*x+31)/((x-5)*(x+5))` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l3-523.json` | 1 | Expand and simplify (4x+1)(3x-4). | `12x^2-13x-4` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l3-527.json` | 1 | Factorise 2x+2y+6kx+6ky completely. | `(x+y)*(2+6*k)` | `factorised_completely` | Canonical is not complete; use `2*(x+y)*(1+3*k)` |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l3-528.json` | 1 | Factorise 4x^2+16x+12. | `(2*x+2)*(2*x+6)` | `factorised_completely` | Canonical is not complete; use `4*(x+1)*(x+3)` |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l3-529.json` | 1 | Simplify ((x+8)/3x)(3x²/(x+8)). | `x` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l3-530.json` | 1 | Simplify 1/(x²-16)+5/(x-4). | `(5*x+21)/((x-4)*(x+4))` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l3-531.json` | 1 | Expand and simplify (2x+3)(2x-6). | `4x^2-6x-18` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l4-502.json` | 1 | Factorise 20x²+140x+225 completely. | `5*(2*x+5)*(2*x+9)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l4-503.json` | 1 | Simplify ((x²-25)/5x)(3x/(x+5)). | `(3*(x-5))/(5)` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l4-504.json` | 1 | Expand and simplify (2x+5y)(3x-3y). | `6*x^2+9*x*y-15*y^2` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l4-507.json` | 1 | Simplify (x+8)²-(x-8)². | `32*x` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l4-508.json` | 1 | Simplify ((x²-64)/4x)(6x/(x+8)). | `(3*(x-8))/(2)` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l4-509.json` | 1 | Simplify 3/(x-3)-4/(x-3)². | `(3*x-13)/(x-3)^2` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l4-511.json` | 1 | Simplify (x+4)²-(x-4)². | `16*x` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l4-512.json` | 1 | Factorise ax+bx+2ay+2by completely. Show the grouping that exposes the repeated factor. | `(a+b)*(x+2*y)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l4-513.json` | 1 | Simplify 2/(x-6)-2/(x-6)². | `(2*x-14)/(x-6)^2` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l4-514.json` | 1 | Factorise ax+bx+5ay+5by completely. Show the grouping that exposes the repeated factor. | `(a+b)*(x+5*y)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l4-515.json` | 1 | Factorise 27x²+99x+72 completely. | `3*(3*x+3)*(3*x+8)` | `factorised_completely` | Canonical is not complete; use `9*(x+1)*(3*x+8)` |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l4-516.json` | 1 | Expand and simplify (3x+4y)(3x-2y). | `9*x^2+6*x*y-8*y^2` | `expanded` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l5-501.json` | 1 | Factorise ax+bx+6ay+6by completely. Show the grouping that exposes the repeated factor. | `(a+b)*(x+6*y)` | `factorised_completely` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l5-502.json` | 1 | Factorise 45x²+90x+45 completely. | `5*(3*x+3)*(3*x+3)` | `factorised_completely` | Canonical is not complete; use `45*(x+1)^2` |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l5-503.json` | 1 | Simplify ((x²-25)/4x²)÷((x-5)/5x). | `(5*(x+5))/(4*x)` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l5-504.json` | 1 | Simplify ((x+8)²-(x-8)²)/32. | `x` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v1/questions/n5-l5-505.json` | 1 | Simplify 1/(x-5)+2/(x+5)-3x/(x²-25). | `-5/((x-5)*(x+5))` | `simplified_fraction` |  |
| `backend_resources/question_bank/g3_math/secondary_2/n5/v2/questions/n5-l2-953.json` | 1 | Expand and simplify (3x - 4)(2x + 5). | `6*x**2+7*x-20` | `expanded` |  |
| `backend_resources/courses/g3_math/secondary_1/n1/v1/lessons/n5-lesson-06.json` | linear-operations-recall | Simplify (4x + 3) + (2x - 5). | `6x-2` | `expanded` |  |
| `backend_resources/courses/g3_math/secondary_1/n1/v1/lessons/n5-lesson-07.json` | simplification-recall | Simplify 2(3x - 4) + x. | `7x-8` | `expanded` |  |
| `backend_resources/courses/g3_math/secondary_1/n1/v1/lessons/n5-lesson-08.json` | factorisation-recall | Factorise 10x + 15 completely. | `5(2x+3)` | `factorised_completely` |  |
| `backend_resources/courses/g3_math/secondary_2/g2/v1/lessons/n5-lesson-09.json` | n5-09-recall | Expand and simplify (x-4)(x+3). | `x^2-x-12` | `expanded` |  |
| `backend_resources/courses/g3_math/secondary_2/g2/v1/lessons/n5-lesson-12.json` | n5-12-recall | Factorise x²-64. | `(x-8)*(x+8)` | `factorised_completely` |  |
| `backend_resources/courses/g3_math/secondary_2/g2/v1/lessons/n5-lesson-13.json` | n5-13-recall | Factorise px+qx+2py+2qy. | `(p+q)*(x+2*y)` | `factorised_completely` |  |
| `backend_resources/courses/g3_math/secondary_2/g2/v1/lessons/n5-lesson-14.json` | n5-14-recall | Factorise x²-5x+6. | `(x-2)*(x-3)` | `factorised_completely` |  |
| `backend_resources/courses/g3_math/secondary_2/g2/v1/lessons/n5-lesson-15.json` | n5-15-recall | Simplify (2a/3b)(9b/4a²). | `3/(2*a)` | `simplified_fraction` |  |
| `backend_resources/courses/g3_math/secondary_2/g2/v1/lessons/n5-lesson-16.json` | n5-16-recall | Simplify 1/(x-3)-2/(x-3)². | `(x-5)/(x-3)^2` | `simplified_fraction` |  |

## Part with no supported form

- `backend_resources/question_bank/g3_math/secondary_1/n5/v1/questions/n5-l2-002.json` part 1: "Write 6m as repeated addition." (canonical `m+m+m+m+m+m`). Every equivalent
  expression passes, including `6m` itself. No form expresses "an unsimplified sum". Recommend replacing
  the item or making it a different response type.

## Percentage parts that rely on the transitional inference

The checker reads a trailing `%` as the unit, not as division by 100, when the response declares
`unit.canonical` = `%`. The 4 N3 lesson recalls already do. Bank parts have no unit, so the checker
also infers a percentage answer when `canonical_latex` is exactly the canonical number followed by `\%`,
which is the answer the learner is shown. The content PRs should add the explicit unit to each part below,
after which the inference can be removed:

```json
"unit": {"canonical": "%", "accepted": ["%", "percent"], "required": false}
```

- `backend_resources/question_bank/g3_math/secondary_1/n3/v1/questions/` (65): n3-l1-001, n3-l1-002, n3-l1-003, n3-l1-006, n3-l1-007, n3-l1-008, n3-l1-011, n3-l1-012, n3-l1-013, n3-l1-016, n3-l1-017, n3-l1-018, n3-l2-001, n3-l2-002, n3-l2-003, n3-l2-004, n3-l2-005, n3-l2-010, n3-l2-011, n3-l2-012, n3-l2-018, n3-l2-019, n3-l2-020, n3-l2-021, n3-l2-026, n3-l2-027, n3-l2-028, n3-l3-001, n3-l3-002, n3-l3-003, n3-l3-007, n3-l3-008, n3-l3-009, n3-l3-010, n3-l3-011, n3-l3-012, n3-l3-015, n3-l3-016, n3-l3-017, n3-l3-018, n3-l3-019, n3-l3-023, n3-l3-024, n3-l3-025, n3-l3-026, n3-l3-027, n3-l3-030, n3-l4-001, n3-l4-002, n3-l4-003, n3-l4-004(2), n3-l4-006, n3-l4-007, n3-l4-010, n3-l4-011, n3-l4-012, n3-l4-013, n3-l4-014, n3-l4-015, n3-l5-001, n3-l5-002, n3-l5-002(3), n3-l5-003(2), n3-l5-004, n3-l5-005(2)
- `backend_resources/question_bank/g3_math/secondary_1/n3/v2/questions/` (4): n3-l3-901, n3-l3-903, n3-l4-902, n3-l4-904

69 bank parts in all. Percentage-point answers are stored without `\%`, so on those parts `6%` still
reads as 0.06 and is marked wrong. The content PRs should decide whether to accept it, for example with a
`percentage points` unit: `n3-l2-007` part 1, `n3-l2-014` part 1, `n3-l2-022` part 1, `n3-l2-029` part 1, `n3-l4-004` part 1, `n3-l4-016` part 1, `n3-l5-002` part 2, `n3-l4-904` part 2.
