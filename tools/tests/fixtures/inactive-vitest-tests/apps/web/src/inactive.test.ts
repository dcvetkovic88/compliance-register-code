import { describe, it, test } from "vitest";

// it("900-B1 a commented-out check", () => {});
/*
test("900-B1 a check in a block comment", () => {});
*/
test.todo("900-B1 a check still to write");
test.skip("900-B1 a skipped check", () => {});
it.skip("900-B1 another skipped check", () => {});
it.todo("900-B1 another check still to write");
test.fixme("900-B1 a check to fix", () => {});
const note = 'it("900-B1 a check inside a string", () => {})';

describe.skip("900-B1 a skipped group", () => {
  it("a check in the skipped group", () => {});
});

describe("900-B1 the screen", () => {
  describe.skip("a skipped inner group", () => {
    it("a check in the skipped inner group", () => {});
  });
});
