from app.domain.notice_period import to_days


def test_one_month_is_thirty_days() -> None:
    assert to_days(1) == 30


def test_twelve_months_have_no_extra_days() -> None:
    assert to_days(12) == 360


def test_thirteen_months_have_five_extra_days() -> None:
    assert to_days(13) == 395
