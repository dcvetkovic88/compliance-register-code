"""Comments that mention the ruff directive in prose, which ruff does not read as a suppression."""

# A ruff suppression: `# noqa` for a line, `# ruff: noqa` or `# flake8: noqa` for the file.
# Ruff reads a directive only when its noqa is followed by a space, a colon or the end of the comment.
PATTERN = r"noqa"  # quoting `# noqa`, the directive, suppresses nothing
