export const SAMPLE_CATALOG = [
  {
    book_id: "RB-001",
    title: "The Cartographer's Lantern",
    author: "Mara Ellison",
    genre: "Historical Fiction",
    price: 18.99,
    stock_status: "in_stock",
    description:
      "A richly imagined story about maps, memory, and the people who redraw the boundaries of home.",
    rating: 4.7,
    promotional_tag: "Staff Pick",
  },
  {
    book_id: "RB-002",
    title: "Small Hours in Orbit",
    author: "Jon Bell",
    genre: "Science Fiction",
    price: 16.5,
    stock_status: "low_stock",
    description:
      "A character-driven space adventure about friendship, difficult choices, and finding a way back.",
    rating: 4.4,
    promotional_tag: "New Release",
  },
];

export const SAMPLE_READER_CONTEXT = {
  reader_id: "reader-7",
  favorite_genres: ["Science Fiction"],
  books_read: ["RB-001"],
  active_challenge: "Riverside Discovery Trail",
  challenge_progress: 65,
  last_visit: "2026-08-01",
};

export function formatCatalog(records) {
  return JSON.stringify(records, null, 2);
}

export function parseCatalogText(text) {
  if (!text.trim()) {
    throw new Error("Paste a catalog JSON array or load the sample catalog.");
  }

  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw new Error("The catalog is not valid JSON. Check commas and brackets.");
  }

  if (!Array.isArray(parsed)) {
    throw new Error("Catalog JSON must be a top-level array of book records.");
  }

  return parsed;
}

export function formatReaderContext(context) {
  return JSON.stringify(context, null, 2);
}

export function parseReaderContextText(text) {
  if (!text.trim()) {
    return null;
  }

  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw new Error("Reader context is not valid JSON. Check commas and brackets.");
  }

  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error("Reader context JSON must be a top-level object.");
  }

  return parsed;
}
