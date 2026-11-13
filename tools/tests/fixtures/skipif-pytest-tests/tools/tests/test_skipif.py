import pytest

pytestmark = pytest.mark.suite_900_B1


@pytest.mark.skipif(True, reason="never runs")
def test_a_check_skipped_by_condition():
    assert False
