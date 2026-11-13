package demo;

import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

@Tag("900-B1")
class DisabledMethodCheckTest {
    @Test
    @Disabled("never runs")
    void aDisabledCheck() {
    }

    @org.junit.jupiter.api.Disabled
    @Test
    void anotherDisabledCheck() {
    }
}

@Disabled
@Tag("900-B1")
class DisabledClassCheckTest {
    @Test
    void aCheckInTheDisabledClass() {
    }
}

@Tag("900-B1")
@Disabled("never runs")
class OtherDisabledClassCheckTest {
    @Test
    void aCheckInTheOtherDisabledClass() {
    }
}
