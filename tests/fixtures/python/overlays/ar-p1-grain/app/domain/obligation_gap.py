from dataclasses import dataclass


@dataclass(frozen=True)
class ObligationGap:
    obligation_id: str
    gap_count: int
