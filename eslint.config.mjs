// Root ESLint configuration of apps/web and packages/* (plan D23; conventions SA-1.1, SA-1.3-4, SA-4-2;
// backend-rules section 3; frontend-rules SA-2.6; T1.10). Every rule here is an error.
import js from "@eslint/js";
import jsxA11y from "eslint-plugin-jsx-a11y";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import tseslint from "typescript-eslint";

// Size limits (SA-2.3-1 to SA-2.3-5): 30 lines per function, 300 per file, 4 parameters, nesting 3, complexity 10.
const sizeLimits = {
  "max-lines": ["error", { max: 300 }],
  "max-lines-per-function": ["error", { max: 30 }],
  "max-params": ["error", 4],
  "max-depth": ["error", 3],
  complexity: ["error", 10],
};

// Names (SA-1.1-1 to SA-1.1-3, SA-1.1-6, SA-1.3-4): camelCase, PascalCase for types and components,
// UPPER_CASE constants, and booleans that read as a yes/no question.
const naming = [
  "error",
  { selector: "default", format: ["camelCase"], leadingUnderscore: "forbid" },
  { selector: "import", format: ["camelCase", "PascalCase"] },
  { selector: "variable", format: ["camelCase", "UPPER_CASE", "PascalCase"] },
  { selector: "function", format: ["camelCase", "PascalCase"] },
  { selector: "typeLike", format: ["PascalCase"] },
  { selector: "enumMember", format: ["UPPER_CASE"] },
  { selector: "objectLiteralProperty", format: null },
  { selector: "typeProperty", format: null },
  {
    selector: ["variable", "parameter", "property", "accessor"],
    types: ["boolean"],
    format: ["PascalCase"],
    prefix: ["is", "has", "can", "should", "was", "will", "IS_", "HAS_", "CAN_"],
  },
];

// Function components and hooks only (SA-2.6-1).
const classComponent =
  "ClassDeclaration[superClass.name=/^(Pure)?Component$/], ClassDeclaration[superClass.property.name=/^(Pure)?Component$/], " +
  "ClassExpression[superClass.name=/^(Pure)?Component$/], ClassExpression[superClass.property.name=/^(Pure)?Component$/]";

export default tseslint.config(
  {
    ignores: ["**/node_modules/**", "**/dist/**", "**/build/**", "**/coverage/**", "**/fixtures/**", "**/generated/**"],
  },
  js.configs.recommended,
  ...tseslint.configs.recommendedTypeChecked,
  {
    files: ["**/*.{ts,tsx,mts,cts}"],
    languageOptions: {
      parserOptions: { projectService: true, ecmaFeatures: { jsx: true } },
    },
    plugins: { react, "react-hooks": reactHooks, "jsx-a11y": jsxA11y },
    settings: { react: { version: "19.3" } },
    rules: {
      ...reactHooks.configs.recommended.rules,
      ...Object.fromEntries(Object.keys(jsxA11y.configs.recommended.rules).map((rule) => [rule, "error"])),
      ...sizeLimits,
      "@typescript-eslint/naming-convention": naming,
      // Unused parameters and variables (SA-2.2-5, SA-2.7-2): every parameter counts.
      "@typescript-eslint/no-unused-vars": ["error", { args: "all", argsIgnorePattern: "^$", caughtErrors: "all" }],
      "no-restricted-syntax": [
        "error",
        { selector: classComponent, message: "Function components and hooks only (SA-2.6-1)." },
      ],
      // Every user-facing string through i18n (SA-2.6-3).
      "react/jsx-no-literals": ["error", { noStrings: true, ignoreProps: true }],
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "error",
    },
  },
  {
    files: ["**/*.{js,mjs,cjs}"],
    extends: [tseslint.configs.disableTypeChecked],
  },
);
