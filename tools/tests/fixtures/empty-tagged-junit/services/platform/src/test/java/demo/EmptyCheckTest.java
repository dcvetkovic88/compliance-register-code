package demo;

import org.junit.jupiter.api.Tag;

@Tag("900-B1")
class EmptyCheckTest {
    void helperThatIsNotATest() {
    }
}

class OtherCheckTest {
    @org.junit.jupiter.api.Test
    void otherSuiteCheck() {
    }
}
