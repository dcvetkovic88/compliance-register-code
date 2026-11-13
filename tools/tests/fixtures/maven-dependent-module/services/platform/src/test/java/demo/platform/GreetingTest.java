package demo.platform;

import static org.junit.jupiter.api.Assertions.assertEquals;

import demo.kit.Greeter;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

@Tag("900-B1")
class GreetingTest {
    @Test
    @DisplayName("900-AC1 the service greets through the library")
    void greetsThroughTheLibrary() {
        assertEquals("hello", new Greeter().greet());
    }

    @Test
    @Disabled("never runs")
    @DisplayName("900-AC2 a disabled acceptance check")
    void disabledAcceptanceCheck() {}
}
