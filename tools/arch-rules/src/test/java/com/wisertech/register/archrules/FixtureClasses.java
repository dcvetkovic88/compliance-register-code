package com.wisertech.register.archrules;

import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.lang.ArchRule;

/** The fixture services and libraries of the tests: one package per violation under services and libs. */
final class FixtureClasses {
    static final String SERVICES = "com.wisertech.register.services.";
    static final String LIBS = "com.wisertech.register.libs.";

    private FixtureClasses() {}

    static JavaClasses importFixtures(String... packages) {
        return new ClassFileImporter().importPackages(packages);
    }

    /** The rule fails on the fixture packages and names the class that breaks it. */
    static void assertViolation(ArchRule rule, String violatingClass, String... packages) {
        AssertionError error = assertThrows(AssertionError.class, () -> rule.check(importFixtures(packages)));
        String message = String.valueOf(error.getMessage());
        assertTrue(message.contains(violatingClass), message);
    }
}
