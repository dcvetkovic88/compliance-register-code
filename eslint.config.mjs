// Root ESLint configuration of apps/web and packages/* (plan D23; conventions SA-1.1, SA-1.3-4, SA-4-2;
// backend-rules section 3; frontend-rules SA-2.6; T1.10). Every rule here is an error.
import path from "node:path";
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

// File and folder names (SA-1.1-4, SA-1.1-5): folders kebab-case, components PascalCase.tsx, other files
// kebab-case.ts. A name's further parts, as in .test.ts or .d.ts, are kebab-case too. naming-convention reads
// identifiers only, so this local rule reads the path of each linted file below the folder ESLint runs in.
const KEBAB_CASE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const PASCAL_CASE = /^[A-Z][A-Za-z0-9]*$/;
const fileAndFolderNames = {
  meta: {
    type: "suggestion",
    schema: [],
    messages: {
      folder: "Folder {{name}} is not kebab-case (SA-1.1-4).",
      component: "File {{name}} is not PascalCase.tsx; a component file is (SA-1.1-5).",
      file: "File {{name}} is not kebab-case; a file other than a component is (SA-1.1-5).",
    },
  },
  create(context) {
    const parts = path.relative(context.cwd, context.filename).split(path.sep);
    const name = parts.pop();
    const [stem, ...rest] = name.split(".");
    const extension = rest.pop();
    const isComponent = extension === "tsx";
    const isStemValid = (isComponent ? PASCAL_CASE : KEBAB_CASE).test(stem);
    return {
      Program(node) {
        for (const folder of parts.filter((part) => part !== ".." && !KEBAB_CASE.test(part))) {
          context.report({ node, messageId: "folder", data: { name: folder } });
        }
        if (!isStemValid || !rest.every((part) => KEBAB_CASE.test(part))) {
          context.report({ node, messageId: isComponent ? "component" : "file", data: { name } });
        }
      },
    };
  },
};
// Every user-facing string through i18n (SA-2.6-3), the text of attributes too. react/jsx-no-literals ignores
// attribute values, since most are technical (className, type, id, href); this local rule reports literal text in
// the attributes a user sees or hears. Add a visible or spoken attribute here when the web starts to use it.
const USER_FACING_PROPS = new Set([
  "placeholder",
  "title",
  "alt",
  "label",
  "aria-label",
  "aria-description",
  "aria-placeholder",
  "aria-roledescription",
  "aria-valuetext",
]);
const isLiteralText = (value) =>
  (value?.type === "Literal" && typeof value.value === "string") ||
  (value?.type === "TemplateLiteral" && value.expressions.length === 0);
const noLiteralUserFacingProps = {
  meta: {
    type: "problem",
    schema: [],
    messages: { literal: "Attribute {{name}} is seen or heard by a user; pass it through i18n (SA-2.6-3)." },
  },
  create(context) {
    return {
      JSXAttribute(node) {
        const name = node.name.type === "JSXIdentifier" ? node.name.name : null;
        const value = node.value?.type === "JSXExpressionContainer" ? node.value.expression : node.value;
        if (USER_FACING_PROPS.has(name) && isLiteralText(value)) {
          context.report({ node, messageId: "literal", data: { name } });
        }
      },
    };
  },
};
const register = {
  rules: { "file-and-folder-names": fileAndFolderNames, "no-literal-user-facing-props": noLiteralUserFacingProps },
};

// Function components and hooks only (SA-2.6-1).
const classComponent =
  "ClassDeclaration[superClass.name=/^(Pure)?Component$/], ClassDeclaration[superClass.property.name=/^(Pure)?Component$/], " +
  "ClassExpression[superClass.name=/^(Pure)?Component$/], ClassExpression[superClass.property.name=/^(Pure)?Component$/]";

// AR-W2: a feature calls a service only through the generated client. dependency-cruiser sees imports of HTTP
// libraries but not the global fetch, so a local wrapper around fetch is caught here: the network globals are
// used only under apps/web/src/api, where the generated clients live.
const NETWORK_GLOBALS = ["fetch", "XMLHttpRequest", "WebSocket", "EventSource"];
const networkMessage = "AR-W2: only the generated clients of apps/web/src/api call a service.";
const networkGlobals = ["error", ...NETWORK_GLOBALS.map((name) => ({ name, message: networkMessage }))];
const networkProperties = [
  "error",
  ...["window", "globalThis", "self"].flatMap((object) =>
    NETWORK_GLOBALS.map((property) => ({ object, property, message: networkMessage })),
  ),
];

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
    plugins: { react, "react-hooks": reactHooks, "jsx-a11y": jsxA11y, register },
    settings: { react: { version: "19.3" } },
    rules: {
      ...reactHooks.configs.recommended.rules,
      ...Object.fromEntries(Object.keys(jsxA11y.configs.recommended.rules).map((rule) => [rule, "error"])),
      ...sizeLimits,
      "@typescript-eslint/naming-convention": naming,
      "register/file-and-folder-names": "error",
      // Unused parameters and variables (SA-2.2-5, SA-2.7-2): every parameter counts.
      "@typescript-eslint/no-unused-vars": ["error", { args: "all", argsIgnorePattern: "^$", caughtErrors: "all" }],
      "no-restricted-syntax": [
        "error",
        { selector: classComponent, message: "Function components and hooks only (SA-2.6-1)." },
      ],
      // Every user-facing string through i18n (SA-2.6-3).
      "react/jsx-no-literals": ["error", { noStrings: true, ignoreProps: true }],
      "register/no-literal-user-facing-props": "error",
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "error",
      "no-restricted-globals": networkGlobals,
      "no-restricted-properties": networkProperties,
    },
  },
  {
    files: ["**/apps/web/src/api/**"],
    rules: { "no-restricted-globals": "off", "no-restricted-properties": "off" },
  },
  {
    files: ["**/*.{js,mjs,cjs}"],
    extends: [tseslint.configs.disableTypeChecked],
  },
);
