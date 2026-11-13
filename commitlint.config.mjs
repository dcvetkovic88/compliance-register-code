// commitlint (T1.8; SA-1.2-15, SA-4-12): Conventional Commits, as feat(register): add exit plan field.
// The subject may start with a task id such as T1.5, so the subject case rule is off.
export default {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "subject-case": [0],
  },
};
