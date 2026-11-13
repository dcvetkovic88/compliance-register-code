import { expect, test } from "vitest";

import { toPageTitle } from "./page-title";

test("the page title names the screen first", () => {
  expect(toPageTitle("Obligations", "Register")).toBe("Obligations | Register");
});
