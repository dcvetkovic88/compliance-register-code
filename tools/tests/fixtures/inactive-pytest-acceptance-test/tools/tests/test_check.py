import pytest

pytestmark = pytest.mark.suite_900_B1


def test_the_check_runs():
    assert True


@pytest.mark.skip(reason="never runs")
def test_900_ac1_a_skipped_acceptance_check():
    assert False


@pytest.mark.parametrize("value", [1, pytest.param(2, id="900-AC1 a skipped case", marks=[pytest.mark.skip])])
def test_the_cases(value):
    assert value
