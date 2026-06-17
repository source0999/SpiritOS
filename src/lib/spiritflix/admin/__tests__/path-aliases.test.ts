import { describe, expect, it } from "vitest";
import { adminPathsEquivalent, expandSpiritFlixPathAliases } from "../path-aliases";

describe("SpiritFlix admin path aliases", () => {
  it("maps host media paths to container aliases", () => {
    const aliases = expandSpiritFlixPathAliases("/mnt/spirit-8tb/media/yes/foo.mkv");
    expect(aliases).toContain("/mnt/spirit-8tb/media/yes/foo.mkv");
    expect(aliases).toContain("/media/yes/foo.mkv");
  });

  it("maps container media paths to host aliases", () => {
    const aliases = expandSpiritFlixPathAliases("/media/movies/Example.mkv");
    expect(aliases).toContain("/media/movies/example.mkv");
    expect(aliases).toContain("/mnt/spirit-8tb/media/movies/example.mkv");
  });

  it("treats host and container paths as equivalent", () => {
    expect(adminPathsEquivalent("/mnt/spirit-8tb/media/yes/foo.mkv", "/media/yes/foo.mkv")).toBe(true);
    expect(adminPathsEquivalent("/mnt/spirit-8tb/media/anime", "/media/anime")).toBe(true);
  });
});
