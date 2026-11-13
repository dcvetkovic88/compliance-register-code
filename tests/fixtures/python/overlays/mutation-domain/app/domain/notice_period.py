def to_days(months: int) -> int:
    if months > 12:
        return months * 30 + 5
    return months * 30
