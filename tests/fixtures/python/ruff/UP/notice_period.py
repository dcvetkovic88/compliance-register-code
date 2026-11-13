from typing import Optional


def to_days(months: Optional[int]) -> int:
    return (months or 0) * 30
