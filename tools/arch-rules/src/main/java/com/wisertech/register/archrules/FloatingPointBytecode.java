package com.wisertech.register.archrules;

import com.tngtech.archunit.core.domain.JavaClass;
import com.tngtech.archunit.core.domain.Source;
import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.util.Arrays;
import java.util.List;
import java.util.Set;
import java.util.stream.Stream;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.Opcodes;
import org.objectweb.asm.Type;
import org.objectweb.asm.tree.AbstractInsnNode;
import org.objectweb.asm.tree.ClassNode;
import org.objectweb.asm.tree.FieldInsnNode;
import org.objectweb.asm.tree.IntInsnNode;
import org.objectweb.asm.tree.InvokeDynamicInsnNode;
import org.objectweb.asm.tree.LdcInsnNode;
import org.objectweb.asm.tree.MethodInsnNode;
import org.objectweb.asm.tree.MethodNode;
import org.objectweb.asm.tree.MultiANewArrayInsnNode;
import org.objectweb.asm.tree.TypeInsnNode;

/**
 * Reads the bytecode of a class for float and double inside its methods: constants, local variables, arithmetic,
 * conversions, and the calls and field reads whose types are float or double, such as
 * {@code BigDecimal.valueOf(0.1 + 0.2)} (AR-J13). Field types and method signatures are ArchUnit's part.
 */
final class FloatingPointBytecode {
    private static final Set<Integer> INSTRUCTIONS = Set.of(
            Opcodes.FCONST_0,
            Opcodes.FCONST_1,
            Opcodes.FCONST_2,
            Opcodes.DCONST_0,
            Opcodes.DCONST_1,
            Opcodes.FLOAD,
            Opcodes.DLOAD,
            Opcodes.FSTORE,
            Opcodes.DSTORE,
            Opcodes.FALOAD,
            Opcodes.DALOAD,
            Opcodes.FASTORE,
            Opcodes.DASTORE,
            Opcodes.FADD,
            Opcodes.DADD,
            Opcodes.FSUB,
            Opcodes.DSUB,
            Opcodes.FMUL,
            Opcodes.DMUL,
            Opcodes.FDIV,
            Opcodes.DDIV,
            Opcodes.FREM,
            Opcodes.DREM,
            Opcodes.FNEG,
            Opcodes.DNEG,
            Opcodes.I2F,
            Opcodes.I2D,
            Opcodes.L2F,
            Opcodes.L2D,
            Opcodes.F2I,
            Opcodes.F2L,
            Opcodes.F2D,
            Opcodes.D2I,
            Opcodes.D2L,
            Opcodes.D2F,
            Opcodes.FCMPL,
            Opcodes.FCMPG,
            Opcodes.DCMPL,
            Opcodes.DCMPG,
            Opcodes.FRETURN,
            Opcodes.DRETURN);

    private static final Set<String> BOXED = Set.of("java/lang/Float", "java/lang/Double");

    private FloatingPointBytecode() {}

    /** The names of the methods of the class that compute with float or double, in class file order. */
    static List<String> methodsUsingFloatingPoint(JavaClass javaClass) {
        return javaClass
                .getSource()
                .map(source -> read(javaClass, source).methods.stream()
                        .filter(FloatingPointBytecode::usesFloatingPoint)
                        .map(method -> method.name)
                        .distinct()
                        .toList())
                .orElse(List.of());
    }

    private static ClassNode read(JavaClass javaClass, Source source) {
        ClassNode node = new ClassNode();
        try (InputStream bytes = source.getUri().toURL().openStream()) {
            new ClassReader(bytes).accept(node, ClassReader.SKIP_DEBUG);
        } catch (IOException e) {
            throw new UncheckedIOException("Cannot read the bytecode of " + javaClass.getName(), e);
        }
        return node;
    }

    private static boolean usesFloatingPoint(MethodNode method) {
        return Arrays.stream(method.instructions.toArray()).anyMatch(FloatingPointBytecode::usesFloatingPoint);
    }

    private static boolean usesFloatingPoint(AbstractInsnNode instruction) {
        return switch (instruction) {
            case LdcInsnNode ldc -> ldc.cst instanceof Float || ldc.cst instanceof Double;
            case IntInsnNode array ->
                array.getOpcode() == Opcodes.NEWARRAY
                        && (array.operand == Opcodes.T_FLOAT || array.operand == Opcodes.T_DOUBLE);
            case TypeInsnNode type -> isFloatingPoint(Type.getObjectType(type.desc));
            case FieldInsnNode field -> describesFloatingPoint(field.desc);
            case MethodInsnNode call -> BOXED.contains(call.owner) || describesFloatingPoint(call.desc);
            case InvokeDynamicInsnNode call -> describesFloatingPoint(call.desc);
            case MultiANewArrayInsnNode array -> describesFloatingPoint(array.desc);
            default -> INSTRUCTIONS.contains(instruction.getOpcode());
        };
    }

    private static boolean describesFloatingPoint(String descriptor) {
        Type type = Type.getType(descriptor);
        if (type.getSort() != Type.METHOD) {
            return isFloatingPoint(type);
        }
        return Stream.concat(Arrays.stream(type.getArgumentTypes()), Stream.of(type.getReturnType()))
                .anyMatch(FloatingPointBytecode::isFloatingPoint);
    }

    private static boolean isFloatingPoint(Type type) {
        if (type.getSort() == Type.ARRAY) {
            return isFloatingPoint(type.getElementType());
        }
        return type.getSort() == Type.FLOAT
                || type.getSort() == Type.DOUBLE
                || (type.getSort() == Type.OBJECT && BOXED.contains(type.getInternalName()));
    }
}
