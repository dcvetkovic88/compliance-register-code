def to_days(years: int, months: int, weeks: int, days: int, hours: int) -> int:
    return years * 365 + months * 30 + weeks * 7 + days + hours // 24
