import { expect, test } from "vitest";

import { toDays } from "./notice-period";

test("one month is thirty days", () => {
  expect(toDays(1)).toBe(30);
});
