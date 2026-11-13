package com.wisertech.register.archrules;

import com.tngtech.archunit.base.DescribedPredicate;
import com.tngtech.archunit.core.domain.JavaClass;
import com.tngtech.archunit.core.domain.JavaCodeUnit;
import com.tngtech.archunit.core.domain.JavaField;
import com.tngtech.archunit.core.domain.JavaModifier;
import com.tngtech.archunit.lang.ArchCondition;
import com.tngtech.archunit.lang.ConditionEvents;
import com.tngtech.archunit.lang.SimpleConditionEvent;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Stream;

/** The conditions the rules need that ArchUnit does not offer. */
final class RuleConditions {
    /** The capability ports of L1 section 5 without the Port suffix; every other port ends in Port. */
    private static final Set<String> PORTS_WITHOUT_SUFFIX = Set.of("DefinitionSource", "ModelGateway");

    private static final Set<String> FLOATING_POINT = Set.of("float", "double", "java.lang.Float", "java.lang.Double");

    static final DescribedPredicate<JavaClass> PORT =
            DescribedPredicate.describe("a port", javaClass -> isPort(javaClass));

    static final DescribedPredicate<JavaClass> PORT_IMPLEMENTATION = DescribedPredicate.describe(
            "implement a port",
            javaClass -> !javaClass.isInterface()
                    && javaClass.getAllRawInterfaces().stream().anyMatch(RuleConditions::isPort));

    private RuleConditions() {}

    private static boolean isPort(JavaClass javaClass) {
        return javaClass.getSimpleName().endsWith("Port") || PORTS_WITHOUT_SUFFIX.contains(javaClass.getSimpleName());
    }

    static ArchCondition<JavaClass> haveRegulationVersionBesideObligationId() {
        return new ArchCondition<>("have a regulationVersion beside an obligationId") {
            @Override
            public void check(JavaClass javaClass, ConditionEvents events) {
                List<String> names =
                        javaClass.getFields().stream().map(JavaField::getName).toList();
                if (names.contains("obligationId") && !names.contains("regulationVersion")) {
                    events.add(SimpleConditionEvent.violated(
                            javaClass, javaClass.getName() + " has an obligationId without a regulationVersion"));
                }
            }
        };
    }

    static ArchCondition<JavaClass> notHaveExactlyOneSubtype() {
        return new ArchCondition<>("not have exactly one implementation or child") {
            @Override
            public void check(JavaClass javaClass, ConditionEvents events) {
                if (javaClass.getSubclasses().size() == 1) {
                    events.add(SimpleConditionEvent.violated(
                            javaClass, javaClass.getName() + " has exactly one implementation or child"));
                }
            }
        };
    }

    static ArchCondition<JavaClass> haveAtMostOnePublicMethod() {
        return new ArchCondition<>("have at most one public method") {
            @Override
            public void check(JavaClass javaClass, ConditionEvents events) {
                long publicMethods = javaClass.getMethods().stream()
                        .filter(method -> method.getModifiers().contains(JavaModifier.PUBLIC))
                        .filter(method -> !isGenerated(method))
                        .count();
                if (publicMethods > 1) {
                    events.add(SimpleConditionEvent.violated(
                            javaClass, javaClass.getName() + " has " + publicMethods + " public methods"));
                }
            }
        };
    }

    static ArchCondition<JavaCodeUnit> notTakeAnOptionalParameter() {
        return new ArchCondition<>("not take an Optional parameter") {
            @Override
            public void check(JavaCodeUnit codeUnit, ConditionEvents events) {
                boolean takesOptional =
                        codeUnit.getRawParameterTypes().stream().anyMatch(type -> type.isEquivalentTo(Optional.class));
                if (takesOptional && !isGenerated(codeUnit)) {
                    events.add(SimpleConditionEvent.violated(
                            codeUnit, codeUnit.getFullName() + " takes an Optional parameter"));
                }
            }
        };
    }

    static ArchCondition<JavaCodeUnit> notTakeOrReturnFloatingPoint() {
        return new ArchCondition<>("not take or return float or double") {
            @Override
            public void check(JavaCodeUnit codeUnit, ConditionEvents events) {
                boolean usesFloatingPoint = Stream.concat(
                                codeUnit.getRawParameterTypes().stream(), Stream.of(codeUnit.getRawReturnType()))
                        .anyMatch(type -> FLOATING_POINT.contains(type.getName()));
                if (usesFloatingPoint && !isGenerated(codeUnit)) {
                    events.add(SimpleConditionEvent.violated(
                            codeUnit, codeUnit.getFullName() + " takes or returns float or double"));
                }
            }
        };
    }

    static ArchCondition<JavaClass> notComputeWithFloatingPoint() {
        return new ArchCondition<>("not compute with float or double inside a method") {
            @Override
            public void check(JavaClass javaClass, ConditionEvents events) {
                for (String method : FloatingPointBytecode.methodsUsingFloatingPoint(javaClass)) {
                    events.add(SimpleConditionEvent.violated(
                            javaClass, javaClass.getName() + "." + method + " computes with float or double"));
                }
            }
        };
    }

    private static boolean isGenerated(JavaCodeUnit codeUnit) {
        return codeUnit.getModifiers().contains(JavaModifier.SYNTHETIC)
                || codeUnit.getModifiers().contains(JavaModifier.BRIDGE);
    }
}
