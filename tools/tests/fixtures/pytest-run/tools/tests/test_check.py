import pytest

pytestmark = pytest.mark.suite_900_B1


def test_900_ac1_the_check_runs():
    assert True


@pytest.mark.skipif(True, reason="never runs")
def test_900_ac2_a_check_skipped_by_condition():
    assert False


@pytest.mark.parametrize("value", [])
def test_900_ac3_a_check_without_cases(value):
    assert False
