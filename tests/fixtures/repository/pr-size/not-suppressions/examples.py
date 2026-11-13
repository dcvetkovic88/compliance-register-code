"""Shows the suppressions the size check recognizes, without using one.

A ruff suppression reads `def parse(a, b, c, d, e, f):  # noqa: PLR0913`.
"""

import re

SUPPRESSION = re.compile(r"noqa:[^\n]*\b(PLR0913|PLR0915|PLR1702|C901)\b")
ANNOTATION = '@SuppressWarnings("PMD.MethodLength") // NOPMD'
ESLINT = "// eslint-disable-next-line max-params"


def example() -> str:
    return "# noqa: C901"  # a comment naming no suppression
