from app.adapters.notice_store import to_row


def test_a_row_names_the_months() -> None:
    assert to_row(2)["months"] == 2
