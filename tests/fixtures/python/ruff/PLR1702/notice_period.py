def count_long(periods: list[list[int]]) -> int:
    count = 0
    for months in periods:
        for month in months:
            if month > 12:
                while month > 24:
                    count += 1
                    month -= 12
    return count
