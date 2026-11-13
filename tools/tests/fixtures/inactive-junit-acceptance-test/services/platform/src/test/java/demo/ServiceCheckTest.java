package demo;

import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

@Tag("900-B1")
class ServiceCheckTest {
    @Test
    void serviceCheckRuns() {
    }

    @Test
    @Disabled("never runs")
    @DisplayName("900-AC1 a disabled acceptance check")
    void disabledAcceptanceCheck() {
    }
}

@Disabled
@Tag("900-B1")
class DisabledServiceCheckTest {
    @Test
    @DisplayName("900-AC1 an acceptance check in a disabled class")
    void acceptanceCheckInADisabledClass() {
    }
}
