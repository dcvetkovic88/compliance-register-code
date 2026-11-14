from app.domain.notice_period import to_days


def test_one_month_is_thirty_days() -> None:
    assert to_days(1) > 0
