import { describe, expect, it } from "vitest";
import { fmtPLabel } from "./format";

describe("fmtPLabel", () => {
  it("uses = before a number", () => {
    expect(fmtPLabel(0.0042)).toBe("p = 0.0042");
    expect(fmtPLabel(0.25, "z-test p")).toBe("z-test p = 0.250");
  });
  it("drops = when the value is a bound", () => {
    expect(fmtPLabel(1e-102, "z-test p")).toBe("z-test p < 0.001");
  });
});
