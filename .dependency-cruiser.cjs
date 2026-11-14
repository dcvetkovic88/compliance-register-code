// dependency-cruiser rules of the web and its packages (plan D23; conventions section 6, AR-W2 to AR-W7; T1.10).
// Run from the repository root: depcruise --config .dependency-cruiser.cjs apps packages
// The generated typed clients (one per service, block 4) live under apps/web/src/api/; nothing else calls a
// service. The component kit (shadcn components, Radix, lucide) lives in packages/shell/ui (plan D16).
const npm = (names) => `(^|node_modules/)(${names.join("|")})(/|$)`;

const HTTP_LIBRARIES = [
  "axios",
  "ky",
  "ofetch",
  "got",
  "superagent",
  "node-fetch",
  "cross-fetch",
  "undici",
  "redaxios",
  "wretch",
];
const DATABASE_CLIENTS = [
  "pg",
  "postgres",
  "mysql",
  "mysql2",
  "sqlite3",
  "better-sqlite3",
  "mongodb",
  "mongoose",
  "redis",
  "ioredis",
  "@prisma/client",
  "typeorm",
  "knex",
  "drizzle-orm",
  "sequelize",
];
const IDENTITY_LIBRARIES = [
  "keycloak-js",
  "keycloak-connect",
  "@react-keycloak/[^/]+",
  "oidc-client",
  "oidc-client-ts",
  "react-oidc-context",
  "openid-client",
  "oauth4webapi",
  "jose",
  "jsonwebtoken",
  "jwt-decode",
  "@auth0/[^/]+",
  "next-auth",
  "@azure/msal-[^/]+",
  "@okta/[^/]+",
];
const COMPONENT_KIT = ["@radix-ui/[^/]+", "lucide-react"];
const API_CLIENTS = "^apps/web/src/api/";
// Components are PascalCase.tsx and other modules kebab-case (conventions SA-1.1-5), so both spellings match.
const SHELL_MODULES = "(^|/)([Hh]eader|[Nn]avigation|[Tt]heme|[Ll]ocale-?[Ss]witch)[^/]*$";
const SHELL = "^packages/shell/";
const TESTS = "\\.(test|e2e)\\.tsx?$";

module.exports = {
  forbidden: [
    {
      name: "AR-W2-http-library-outside-the-clients",
      comment:
        "AR-W2: a feature calls a service only through the generated client; HTTP libraries are imported nowhere else. " +
        "A local wrapper around the global fetch is no import; eslint.config.mjs rejects fetch outside the clients.",
      severity: "error",
      from: { path: "^(apps|packages)/", pathNot: API_CLIENTS },
      to: { path: npm(HTTP_LIBRARIES) },
    },
    {
      name: "AR-W3-database-client",
      comment: "AR-W3, AR-W6: the web and its packages import no database client.",
      severity: "error",
      from: { path: "^(apps|packages)/" },
      to: { path: npm(DATABASE_CLIENTS) },
    },
    {
      name: "AR-W3-services-and-libraries",
      comment: "AR-W3, AR-W6: the web and its packages import nothing from services/ or libs/.",
      severity: "error",
      from: { path: "^(apps|packages)/" },
      to: { path: "^(services|libs)/" },
    },
    {
      name: "AR-W4-identity-library",
      comment: "AR-W4: no OIDC, token or Keycloak library in apps/web or packages/; the BFF holds the session.",
      severity: "error",
      from: { path: "^(apps/web|packages)/" },
      to: { path: npm(IDENTITY_LIBRARIES) },
    },
    {
      name: "AR-W5-component-kit-outside-the-shell",
      comment: "AR-W5: a feature imports the component kit only through packages/shell.",
      severity: "error",
      from: { path: "^apps/" },
      to: { path: npm(COMPONENT_KIT) },
    },
    {
      name: "AR-W5-shell-imports-the-web",
      comment: "AR-W5: packages/shell never imports apps/web.",
      severity: "error",
      from: { path: SHELL },
      to: { path: "^apps/web/" },
    },
    {
      name: "AR-W5-feature-imports-another-feature",
      comment: "AR-W5: a feature never imports another feature.",
      severity: "error",
      from: { path: "^apps/web/src/features/([^/]+)/" },
      to: { path: "^apps/web/src/features/", pathNot: "^apps/web/src/features/$1/" },
    },
    {
      name: "AR-W5-shell-module-outside-the-shell",
      comment: "AR-W5: header, navigation, theme and locale switch exist only under packages/shell.",
      severity: "error",
      from: { path: "^(apps|packages)/" },
      to: { path: `^(apps|packages)/.*${SHELL_MODULES}`, pathNot: SHELL },
    },
    {
      name: "AR-W5-shell-module-outside-the-shell-imports",
      comment: "AR-W5: header, navigation, theme and locale switch exist only under packages/shell.",
      severity: "error",
      from: { path: `^(apps|packages)/.*${SHELL_MODULES}`, pathNot: SHELL },
      to: {},
    },
    {
      name: "AR-W7-component-imports-a-client",
      comment: "AR-W7: components do not import the API clients directly; hooks and services do.",
      severity: "error",
      from: { path: "^apps/web/src/.*\\.tsx$", pathNot: [API_CLIENTS, TESTS] },
      to: { path: API_CLIENTS },
    },
  ],
  options: {
    doNotFollow: { path: "node_modules" },
    exclude: { path: "(^|/)(node_modules|dist|coverage|fixtures|generated)/" },
    tsPreCompilationDeps: true,
    enhancedResolveOptions: { extensions: [".ts", ".tsx", ".mts", ".js", ".mjs"] },
  },
};
