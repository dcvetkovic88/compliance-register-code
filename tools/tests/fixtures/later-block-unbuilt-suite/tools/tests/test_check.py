import pytest


@pytest.mark.suite_900_B1
def test_900_ac1_the_check_passes():
    assert True


class TestSecondCheck:
    pytestmark = [pytest.mark.suite_900_B2]

    @pytest.mark.parametrize("value", [1], ids=["900-AC2 the second check passes"])
    def test_second_check(self, value):
        assert value
