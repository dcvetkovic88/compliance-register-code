package demo;

/**
 * Shows the suppressions the size check recognizes, without using one.
 *
 * <pre>
 * @SuppressWarnings("PMD.MethodLength") // NOPMD
 * </pre>
 */
final class Examples {
    // A line comment naming @SuppressWarnings("PMD.ClassLength") suppresses nothing.
    /* Nor does a block comment naming @SuppressWarnings("all"). */
    static final String ANNOTATION = "@SuppressWarnings(\"PMD.MethodLength\") // NOPMD";
    static final String BLOCK = """
        @SuppressWarnings("PMD")
        void map() { // NOPMD
        """;
    static final char QUOTE = '"';

    @SuppressWarnings("unchecked")
    String example() {
        return "// NOPMD " + QUOTE + "@SuppressWarnings(\"all\")";
    }
}
