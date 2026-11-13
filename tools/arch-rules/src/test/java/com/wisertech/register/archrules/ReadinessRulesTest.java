package com.wisertech.register.archrules;

import static com.wisertech.register.archrules.FixtureClasses.LIBS;
import static com.wisertech.register.archrules.FixtureClasses.SERVICES;
import static com.wisertech.register.archrules.FixtureClasses.assertViolation;
import static com.wisertech.register.archrules.FixtureClasses.importFixtures;

import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.lang.ArchRule;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/** The ArchUnit rules of the six suite readiness rules (conventions section 6), each on a violating fixture. */
@Tag("111-B1b")
class ReadinessRulesTest {
    @Test
    @DisplayName("111-AC17 every rule passes on the clean service fixture")
    void everyRulePassesOnTheCleanFixture() {
        JavaClasses clean = importFixtures(SERVICES + "clean", LIBS + "clean");

        for (ArchRule rule : ArchitectureRules.ALL) {
            rule.check(clean);
        }
    }

    @Test
    @DisplayName("111-AC17 AR-J1 fails on an obligation id without its regulation version")
    void obligationWithoutRegulationVersion() {
        assertViolation(
                ArchitectureRules.OBLIGATION_WITH_REGULATION_VERSION, "arj1.domain.Obligation", SERVICES + "arj1");
    }

    @Test
    @DisplayName("111-AC17 AR-J2 fails on a port that is a class")
    void portThatIsAClass() {
        assertViolation(ArchitectureRules.CAPABILITIES_THROUGH_PORTS, "EvidencePort", SERVICES + "arj2class");
    }

    @Test
    @DisplayName("111-AC17 AR-J2 fails on a port implemented outside adapters.out")
    void portImplementedOutsideAdaptersOut() {
        assertViolation(ArchitectureRules.CAPABILITIES_THROUGH_PORTS, "DirectAudit", SERVICES + "arj2impl");
    }

    @Test
    @DisplayName("111-AC17 AR-J2 fails on a domain class that names a stand-in")
    void domainNamingAStandIn() {
        assertViolation(ArchitectureRules.CAPABILITIES_THROUGH_PORTS, "Greeting", SERVICES + "arj2standin");
    }

    @Test
    @DisplayName("111-AC17 AR-J3 fails on a JDBC type outside adapters.out.persistence")
    void jdbcOutsidePersistence() {
        assertViolation(ArchitectureRules.OWN_SCHEMA_AND_CODE, "CountArrangements", SERVICES + "arj3jdbc");
    }

    @Test
    @DisplayName("111-AC17 AR-J3 fails on a service that imports another service")
    void serviceImportingAnotherService() {
        assertViolation(
                ArchitectureRules.OWN_SCHEMA_AND_CODE,
                "arj3first.domain.Provider",
                SERVICES + "arj3first",
                SERVICES + "arj3second");
    }

    @Test
    @DisplayName("111-AC17 AR-J4 fails on a Keycloak type, even in the identity adapter")
    void keycloakType() {
        assertViolation(ArchitectureRules.GENERIC_OIDC, "TokenReader", SERVICES + "arj4keycloak");
    }

    @Test
    @DisplayName("111-AC17 AR-J4 fails on a token library type outside the identity adapter")
    void tokenLibraryOutsideIdentity() {
        assertViolation(ArchitectureRules.GENERIC_OIDC, "SessionController", SERVICES + "arj4token");
    }

    @Test
    @DisplayName("111-AC17 AR-J4 fails on a token library type in an identity package outside the adapters")
    void tokenLibraryInIdentityOutsideAdapters() {
        assertViolation(ArchitectureRules.GENERIC_OIDC, "SessionTokens", SERVICES + "arj4identity");
    }

    @Test
    @DisplayName("111-AC17 AR-J6 fails on a library with a domain package")
    void libraryWithDomain() {
        assertViolation(ArchitectureRules.LIBRARIES_WITHOUT_DOMAIN, "Criticality", LIBS + "arj6domain");
    }

    @Test
    @DisplayName("111-AC17 AR-J6 fails on a library that depends on a service")
    void libraryDependingOnAService() {
        assertViolation(
                ArchitectureRules.LIBRARIES_WITHOUT_DOMAIN,
                "ProviderNames",
                LIBS + "arj6service",
                SERVICES + "arj6target");
    }
}
