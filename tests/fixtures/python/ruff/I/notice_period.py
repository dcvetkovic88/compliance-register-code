import sys
import os


def to_days(months: int) -> int:
    return months * 30 + len(os.sep) + len(sys.argv)
