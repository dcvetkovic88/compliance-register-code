from dataclasses import dataclass


@dataclass(frozen=True)
class ObligationLink:
    obligation_id: str
    regulation_version: str
