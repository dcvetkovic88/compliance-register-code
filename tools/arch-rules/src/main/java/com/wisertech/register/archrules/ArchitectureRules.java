package com.wisertech.register.archrules;

import static com.tngtech.archunit.core.domain.properties.HasName.Predicates.nameMatching;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.classes;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.codeUnits;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.fields;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noFields;
import static com.tngtech.archunit.library.dependencies.SlicesRuleDefinition.slices;
import static com.wisertech.register.archrules.RegisterPackages.ADAPTERS;
import static com.wisertech.register.archrules.RegisterPackages.ADAPTERS_IN;
import static com.wisertech.register.archrules.RegisterPackages.ADAPTERS_OUT;
import static com.wisertech.register.archrules.RegisterPackages.APPLICATION;
import static com.wisertech.register.archrules.RegisterPackages.DOMAIN;
import static com.wisertech.register.archrules.RegisterPackages.FRAMEWORKS;
import static com.wisertech.register.archrules.RegisterPackages.IDENTITY;
import static com.wisertech.register.archrules.RegisterPackages.JAVA_NET_CLIENTS;
import static com.wisertech.register.archrules.RegisterPackages.JDBC;
import static com.wisertech.register.archrules.RegisterPackages.LIBS;
import static com.wisertech.register.archrules.RegisterPackages.PERSISTENCE;
import static com.wisertech.register.archrules.RegisterPackages.PROBLEM_TYPES;
import static com.wisertech.register.archrules.RegisterPackages.REGISTER;
import static com.wisertech.register.archrules.RegisterPackages.REMOTE_CLIENTS;
import static com.wisertech.register.archrules.RegisterPackages.SERVICES;
import static com.wisertech.register.archrules.RegisterPackages.SERVICE_SLICES;
import static com.wisertech.register.archrules.RegisterPackages.TOKEN_LIBRARIES;
import static com.wisertech.register.archrules.RuleConditions.PORT;
import static com.wisertech.register.archrules.RuleConditions.PORT_IMPLEMENTATION;

import com.tngtech.archunit.core.domain.JavaModifier;
import com.tngtech.archunit.junit.ArchTest;
import com.tngtech.archunit.lang.ArchRule;
import com.tngtech.archunit.lang.CompositeArchRule;
import com.tngtech.archunit.library.GeneralCodingRules;
import java.util.Calendar;
import java.util.Date;
import java.util.List;
import java.util.Optional;

/**
 * The shared ArchUnit rules AR-J0 to AR-J13 of conventions section 6 (plan D2, D23). Rules AR-J1 to AR-J4 and
 * AR-J6 are the Java form of the suite readiness rules of L1 section 11; AR-J5 does not exist, because suite
 * readiness rule 5 is about the React shell. Every rule holds when a service has nothing it applies to.
 */
public final class ArchitectureRules {
    @ArchTest
    public static final ArchRule DOMAIN_WITHOUT_FRAMEWORK_TYPES = noClasses()
            .that()
            .resideInAPackage(DOMAIN)
            .should()
            .dependOnClassesThat()
            .resideInAnyPackage(FRAMEWORKS)
            .allowEmptyShould(true)
            .as("AR-J0 domain imports no Spring, JDBC, servlet, HTTP client, JSON, JPA or Keycloak type");

    /** Suite readiness rule 1, shared grain: an obligation is always read with its regulation version. */
    @ArchTest
    public static final ArchRule OBLIGATION_WITH_REGULATION_VERSION = classes()
            .should(RuleConditions.haveRegulationVersionBesideObligationId())
            .allowEmptyShould(true)
            .as("AR-J1 a type with an obligationId also has a regulationVersion (suite readiness rule 1)");

    /** Suite readiness rule 2, ports with stand-ins. */
    @ArchTest
    public static final ArchRule CAPABILITIES_THROUGH_PORTS = CompositeArchRule.of(classes()
                    .that(PORT)
                    .should()
                    .beInterfaces()
                    .andShould()
                    .resideInAnyPackage(DOMAIN, APPLICATION)
                    .allowEmptyShould(true))
            .and(classes()
                    .that(PORT_IMPLEMENTATION)
                    .should()
                    .resideInAPackage(ADAPTERS_OUT)
                    .allowEmptyShould(true))
            .and(noClasses()
                    .that()
                    .resideOutsideOfPackage(ADAPTERS_OUT)
                    .should()
                    .dependOnClassesThat()
                    .haveSimpleNameEndingWith("StandIn")
                    .allowEmptyShould(true))
            .and(noClasses()
                    .that()
                    .resideInAPackage(SERVICES)
                    .and()
                    .resideOutsideOfPackage(ADAPTERS_OUT)
                    .should()
                    .dependOnClassesThat()
                    .resideInAnyPackage(REMOTE_CLIENTS)
                    .orShould()
                    .dependOnClassesThat(nameMatching(JAVA_NET_CLIENTS))
                    .allowEmptyShould(true))
            .as("AR-J2 a suite capability is reached through its port, an interface of domain or application"
                    + " implemented in adapters.out; only adapters.out names a stand-in or an HTTP or remote call"
                    + " client (suite readiness rule 2)");

    /** Suite readiness rule 3, one PostgreSQL engine and one schema per service. */
    @ArchTest
    public static final ArchRule OWN_SCHEMA_AND_CODE = CompositeArchRule.of(noClasses()
                    .that()
                    .resideInAPackage(SERVICES)
                    .and()
                    .resideOutsideOfPackage(PERSISTENCE)
                    .should()
                    .dependOnClassesThat()
                    .resideInAnyPackage(JDBC)
                    .allowEmptyShould(true))
            .and(slices().matching(SERVICE_SLICES)
                    .should()
                    .notDependOnEachOther()
                    .allowEmptyShould(true))
            .as("AR-J3 JDBC types appear only in adapters.out.persistence and no service imports another"
                    + " service (suite readiness rule 3)");

    /** Suite readiness rule 4, generic OIDC. The allowed list for Keycloak types is empty (conventions SA-4-16). */
    @ArchTest
    public static final ArchRule GENERIC_OIDC = CompositeArchRule.of(noClasses()
                    .should()
                    .dependOnClassesThat()
                    .resideInAPackage("org.keycloak..")
                    .allowEmptyShould(true))
            .and(noClasses()
                    .that()
                    .resideOutsideOfPackage(IDENTITY)
                    .should()
                    .dependOnClassesThat()
                    .resideInAnyPackage(TOKEN_LIBRARIES)
                    .allowEmptyShould(true))
            .as("AR-J4 no Keycloak type anywhere, and OAuth and token library types only in an identity adapter"
                    + " (suite readiness rule 4)");

    /** Suite readiness rule 6, the language rule: libraries carry no domain rule. */
    @ArchTest
    public static final ArchRule LIBRARIES_WITHOUT_DOMAIN = CompositeArchRule.of(noClasses()
                    .that()
                    .resideInAPackage(LIBS)
                    .should()
                    .resideInAPackage(DOMAIN)
                    .allowEmptyShould(true))
            .and(noClasses()
                    .that()
                    .resideInAPackage(LIBS)
                    .should()
                    .dependOnClassesThat()
                    .resideInAPackage(SERVICES)
                    .allowEmptyShould(true))
            .as("AR-J6 libs has no domain package and depends on no service (suite readiness rule 6)");

    @ArchTest
    public static final ArchRule LAYER_DIRECTION = CompositeArchRule.of(noClasses()
                    .that()
                    .resideInAnyPackage(DOMAIN, APPLICATION)
                    .should()
                    .dependOnClassesThat()
                    .resideInAPackage(ADAPTERS)
                    .allowEmptyShould(true))
            .and(noClasses()
                    .that()
                    .resideInAPackage(DOMAIN)
                    .should()
                    .dependOnClassesThat()
                    .resideInAPackage(APPLICATION)
                    .allowEmptyShould(true))
            .as("AR-J7 adapters.in -> application -> domain: domain and application never import adapters,"
                    + " and domain never imports application");

    @ArchTest
    public static final ArchRule ONE_USE_CASE_PER_CLASS = classes()
            .that()
            .resideInAPackage(APPLICATION)
            .and()
            .areNotInterfaces()
            .and()
            .areNotRecords()
            .and()
            .areNotEnums()
            .and()
            .areNotAssignableTo(Throwable.class)
            .should(RuleConditions.haveAtMostOnePublicMethod())
            .allowEmptyShould(true)
            .as("AR-J8 one public method per class in application: one use case per class");

    @ArchTest
    public static final ArchRule NO_SPECULATIVE_ABSTRACTION = CompositeArchRule.of(classes()
                    .that()
                    .resideInAPackage(REGISTER)
                    .and()
                    .areInterfaces()
                    .and()
                    .areNotAnnotations()
                    .and(PORT.negate())
                    .should(RuleConditions.notHaveExactlyOneSubtype())
                    .allowEmptyShould(true))
            .and(classes()
                    .that()
                    .resideInAPackage(REGISTER)
                    .and()
                    .areNotInterfaces()
                    .and()
                    .areNotEnums()
                    .and()
                    .haveModifier(JavaModifier.ABSTRACT)
                    .should(RuleConditions.notHaveExactlyOneSubtype())
                    .allowEmptyShould(true))
            .as("AR-J9 no interface with a single implementation unless it is a port, and no abstract class"
                    + " with one child");

    @ArchTest
    public static final ArchRule CONSTRUCTOR_INJECTION = GeneralCodingRules.NO_CLASSES_SHOULD_USE_FIELD_INJECTION
            .allowEmptyShould(true)
            .as("AR-J10 constructor injection only, no field injection");

    @ArchTest
    public static final ArchRule OPTIONAL_ONLY_AS_RETURN_TYPE = CompositeArchRule.of(
                    noFields().should().haveRawType(Optional.class).allowEmptyShould(true))
            .and(codeUnits().should(RuleConditions.notTakeAnOptionalParameter()).allowEmptyShould(true))
            .as("AR-J11 Optional only as a return type, never as a field or parameter");

    @ArchTest
    public static final ArchRule PROBLEM_RESPONSES_IN_ADAPTERS_IN = noClasses()
            .that()
            .resideOutsideOfPackage(ADAPTERS_IN)
            .should()
            .dependOnClassesThat(nameMatching(PROBLEM_TYPES))
            .allowEmptyShould(true)
            .as("AR-J12 problem response types only in adapters.in");

    @ArchTest
    public static final ArchRule EXACT_NUMBERS_AND_TIME_IN_DOMAIN = CompositeArchRule.of(noClasses()
                    .that()
                    .resideInAPackage(DOMAIN)
                    .should()
                    .dependOnClassesThat()
                    .areAssignableTo(Date.class)
                    .orShould()
                    .dependOnClassesThat()
                    .areAssignableTo(Calendar.class)
                    .allowEmptyShould(true))
            .and(fields().that()
                    .areDeclaredInClassesThat()
                    .resideInAPackage(DOMAIN)
                    .should()
                    .notHaveRawType(float.class)
                    .andShould()
                    .notHaveRawType(double.class)
                    .andShould()
                    .notHaveRawType(Float.class)
                    .andShould()
                    .notHaveRawType(Double.class)
                    .allowEmptyShould(true))
            .and(codeUnits()
                    .that()
                    .areDeclaredInClassesThat()
                    .resideInAPackage(DOMAIN)
                    .should(RuleConditions.notTakeOrReturnFloatingPoint())
                    .allowEmptyShould(true))
            .and(classes()
                    .that()
                    .resideInAPackage(DOMAIN)
                    .should(RuleConditions.notComputeWithFloatingPoint())
                    .allowEmptyShould(true))
            .as("AR-J13 no float, double, java.util.Date or Calendar in domain");

    /** Every rule, in the order of their ids. */
    public static final List<ArchRule> ALL = List.of(
            DOMAIN_WITHOUT_FRAMEWORK_TYPES,
            OBLIGATION_WITH_REGULATION_VERSION,
            CAPABILITIES_THROUGH_PORTS,
            OWN_SCHEMA_AND_CODE,
            GENERIC_OIDC,
            LIBRARIES_WITHOUT_DOMAIN,
            LAYER_DIRECTION,
            ONE_USE_CASE_PER_CLASS,
            NO_SPECULATIVE_ABSTRACTION,
            CONSTRUCTOR_INJECTION,
            OPTIONAL_ONLY_AS_RETURN_TYPE,
            PROBLEM_RESPONSES_IN_ADAPTERS_IN,
            EXACT_NUMBERS_AND_TIME_IN_DOMAIN);

    private ArchitectureRules() {}
}
