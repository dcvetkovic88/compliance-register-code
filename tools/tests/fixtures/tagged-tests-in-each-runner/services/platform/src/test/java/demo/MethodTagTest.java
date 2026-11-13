package demo;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

class MethodTagTest {
    @Test
    @Tag("900-B1")
    @DisplayName("900-AC1 the service check passes")
    void serviceCheckPasses() {
    }
}
