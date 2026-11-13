/**
 * Shows the suppressions the size check recognizes, without using one:
 * a comment such as eslint-disable-next-line max-params is one only at the start of a comment.
 */
export const DIRECTIVE = "// eslint-disable-next-line max-params";
export const BLOCK = '/* eslint-disable max-lines */';
export const TEMPLATE = `/* eslint-disable complexity */ ${DIRECTIVE}`;
// The PMD rule PMD.MethodLength and @SuppressWarnings("PMD") are Java, not TypeScript.
