import pytest

pytestmark = [pytest.mark.suite_900_B1, pytest.mark.skip(reason="never runs")]


def test_a_check_in_a_skipped_module():
    assert False
