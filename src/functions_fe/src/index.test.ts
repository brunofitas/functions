import { describe, it, expect } from "vitest";
import { VERSION } from "./index";

describe("functions-fe", () => {
  it("exposes a version", () => {
    expect(VERSION).toBeTruthy();
  });
});
