import { describe, expect, it } from "vitest";
import {
  formatCatalog,
  formatReaderContext,
  parseCatalogText,
  parseReaderContextText,
  SAMPLE_CATALOG,
  SAMPLE_READER_CONTEXT,
} from "./catalog";

describe("catalog input helpers", () => {
  it("formats and parses the included sample catalog", () => {
    const text = formatCatalog(SAMPLE_CATALOG);

    expect(parseCatalogText(text)).toEqual(SAMPLE_CATALOG);
  });

  it("rejects empty, malformed, and non-array input", () => {
    expect(() => parseCatalogText("  ")).toThrow("Paste a catalog JSON array");
    expect(() => parseCatalogText("{not json")).toThrow("not valid JSON");
    expect(() => parseCatalogText('{"records": []}')).toThrow("top-level array");
  });

  it("formats and parses optional reader context", () => {
    expect(parseReaderContextText(formatReaderContext(SAMPLE_READER_CONTEXT))).toEqual(
      SAMPLE_READER_CONTEXT,
    );
    expect(parseReaderContextText("  ")).toBeNull();
    expect(() => parseReaderContextText("[]")).toThrow("top-level object");
  });
});
