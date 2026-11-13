import pytest

pytestmark = pytest.mark.suite_900_B1


@pytest.mark.parametrize("value", [])
def test_a_check_without_cases(value):
    assert False
