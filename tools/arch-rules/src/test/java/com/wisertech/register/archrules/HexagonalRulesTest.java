package com.wisertech.register.archrules;

import static com.wisertech.register.archrules.FixtureClasses.SERVICES;
import static com.wisertech.register.archrules.FixtureClasses.assertViolation;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/** The hexagonal and Java rules (conventions sections 6 and 11), each on a violating fixture. */
@Tag("111-B1b")
class HexagonalRulesTest {
    @Test
    @DisplayName("111-AC17 AR-J0 fails on a domain class that uses a Spring type")
    void domainWithFrameworkType() {
        assertViolation(ArchitectureRules.DOMAIN_WITHOUT_FRAMEWORK_TYPES, "arj0.domain.Arrangement", SERVICES + "arj0");
    }

    @Test
    @DisplayName("111-AC17 AR-J7 fails on an application class that names an adapter")
    void applicationNamingAnAdapter() {
        assertViolation(
                ArchitectureRules.LAYER_DIRECTION, "arj7adapter.application.ApproveRequest", SERVICES + "arj7adapter");
    }

    @Test
    @DisplayName("111-AC17 AR-J7 fails on a domain class that names the application layer")
    void domainNamingTheApplication() {
        assertViolation(ArchitectureRules.LAYER_DIRECTION, "arj7domain.domain.Approval", SERVICES + "arj7domain");
    }

    @Test
    @DisplayName("111-AC17 AR-J8 fails on an application class with two public methods")
    void applicationClassWithTwoUseCases() {
        assertViolation(ArchitectureRules.ONE_USE_CASE_PER_CLASS, "ArrangementService", SERVICES + "arj8");
    }

    @Test
    @DisplayName("111-AC17 AR-J9 fails on an interface with one implementation that is not a port")
    void interfaceWithOneImplementation() {
        assertViolation(ArchitectureRules.NO_SPECULATIVE_ABSTRACTION, "RiskScoring", SERVICES + "arj9interface");
    }

    @Test
    @DisplayName("111-AC17 AR-J9 fails on an abstract class with one child")
    void abstractClassWithOneChild() {
        assertViolation(ArchitectureRules.NO_SPECULATIVE_ABSTRACTION, "Notice", SERVICES + "arj9abstract");
    }

    @Test
    @DisplayName("111-AC17 AR-J10 fails on field injection")
    void fieldInjection() {
        assertViolation(ArchitectureRules.CONSTRUCTOR_INJECTION, "ProviderController", SERVICES + "arj10");
    }

    @Test
    @DisplayName("111-AC17 AR-J11 fails on an Optional field")
    void optionalField() {
        assertViolation(ArchitectureRules.OPTIONAL_ONLY_AS_RETURN_TYPE, "ExitPlan.reviewerId", SERVICES + "arj11field");
    }

    @Test
    @DisplayName("111-AC17 AR-J11 fails on an Optional parameter")
    void optionalParameter() {
        assertViolation(
                ArchitectureRules.OPTIONAL_ONLY_AS_RETURN_TYPE, "describeReviewer", SERVICES + "arj11parameter");
    }

    @Test
    @DisplayName("111-AC17 AR-J12 fails on a problem response outside adapters.in")
    void problemResponseOutsideAdaptersIn() {
        assertViolation(ArchitectureRules.PROBLEM_RESPONSES_IN_ADAPTERS_IN, "RejectRequest", SERVICES + "arj12");
    }

    @Test
    @DisplayName("111-AC17 AR-J13 fails on a double in the domain")
    void doubleInTheDomain() {
        assertViolation(ArchitectureRules.EXACT_NUMBERS_AND_TIME_IN_DOMAIN, "PenaltyRate", SERVICES + "arj13double");
    }

    @Test
    @DisplayName("111-AC17 AR-J13 fails on a double computed inside a domain method")
    void localDoubleInTheDomain() {
        assertViolation(ArchitectureRules.EXACT_NUMBERS_AND_TIME_IN_DOMAIN, "FeeTotal", SERVICES + "arj13localdouble");
    }

    @Test
    @DisplayName("111-AC17 AR-J13 fails on double arithmetic inside a domain method that returns an integer")
    void doubleArithmeticInTheDomain() {
        assertViolation(ArchitectureRules.EXACT_NUMBERS_AND_TIME_IN_DOMAIN, "NoticeDays", SERVICES + "arj13arithmetic");
    }

    @Test
    @DisplayName("111-AC17 AR-J13 fails on java.util.Date in the domain")
    void legacyDateInTheDomain() {
        assertViolation(ArchitectureRules.EXACT_NUMBERS_AND_TIME_IN_DOMAIN, "ReviewDate", SERVICES + "arj13date");
    }
}
