"""A module every ruff rule of the root configuration accepts."""

from dataclasses import dataclass


@dataclass(frozen=True)
class NoticePeriod:
    months: int

    def to_days(self) -> int:
        return self.months * 30
