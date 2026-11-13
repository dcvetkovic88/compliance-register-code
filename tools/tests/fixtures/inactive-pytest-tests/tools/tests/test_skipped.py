import pytest

pytestmark = pytest.mark.suite_900_B1


@pytest.mark.skip(reason="never runs")
def test_a_skipped_check():
    assert False


@pytest.mark.parametrize("value", [pytest.param(1, id="a-skipped-case", marks=pytest.mark.skip)])
def test_only_skipped_cases(value):
    assert False


@pytest.mark.skip
class TestASkippedGroup:
    def test_a_check_in_the_skipped_group(self):
        assert False


class TestAGroupWithASkipMark:
    pytestmark = [pytest.mark.skip(reason="never runs")]

    def test_a_check_under_the_class_skip_mark(self):
        assert False
