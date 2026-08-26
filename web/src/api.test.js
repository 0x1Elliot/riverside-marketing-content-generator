import { afterEach, describe, expect, it, vi } from "vitest";
import { generateMarketingDrafts } from "./api";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("generateMarketingDrafts", () => {
  it("posts the catalog to the configured API and returns its structured result", async () => {
    const catalog = [{ book_id: "RB-001", title: "A Book" }];
    const payload = { generated_drafts: [], rejected_records: [], summary: {} };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: vi.fn().mockResolvedValue(payload),
    });
    vi.stubEnv("VITE_API_BASE_URL", "https://api.example.test/");
    vi.stubGlobal("fetch", fetchMock);

    await expect(generateMarketingDrafts(catalog)).resolves.toEqual(payload);
    expect(fetchMock).toHaveBeenCalledWith(
      "https://api.example.test/generate",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(catalog),
      }),
    );
  });

  it("turns an API error response into a user-readable error", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://api.example.test");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: vi.fn().mockResolvedValue({ detail: "Service unavailable" }),
      }),
    );

    await expect(generateMarketingDrafts([])).rejects.toThrow(
      "Service unavailable (HTTP 503)",
    );
  });

  it("wraps catalog and reader context for the engagement API shape", async () => {
    const catalog = [{ book_id: "RB-001" }];
    const readerContext = { reader_id: "reader-7", favorite_genres: ["Mystery"] };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: vi.fn().mockResolvedValue({ engagement_messages: [] }),
    });
    vi.stubEnv("VITE_API_BASE_URL", "https://api.example.test");
    vi.stubGlobal("fetch", fetchMock);

    await generateMarketingDrafts(catalog, readerContext);

    expect(fetchMock.mock.calls[0][1].body).toBe(
      JSON.stringify({ catalog, reader_context: readerContext }),
    );
  });
});
