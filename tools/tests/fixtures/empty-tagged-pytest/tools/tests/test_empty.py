import pytest

pytestmark = pytest.mark.suite_900_B1


@pytest.mark.suite_900_B1
def helper_that_is_not_a_test():
    return "suite_900_B1"
