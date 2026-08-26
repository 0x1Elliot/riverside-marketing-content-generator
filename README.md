# Riverside Books Marketing Content Generator

## Product D — Marketing Content & Generation System

The Riverside Books Marketing Content Generator is a product component designed to transform structured book data and optional reader context into customer-facing marketing content.

This repository represents my individual contribution to the Riverside Books product suite. While Riverside Books is being developed as a larger multi-product system, this particular repository focuses specifically on **Product D: Marketing Content Generator**.

## Product Role

The purpose of this product is to help Riverside Books create engaging marketing materials from shared catalog data.

The system takes structured book information and generates content that can be used for customer engagement, including:

- Promotional book descriptions
- Marketing campaigns
- Social media content
- Customer-facing recommendations
- Personalized reading engagement messages

## How It Fits Into Riverside Books

Riverside Books is being developed as a four-product suite where each product is built independently and later integrated into a larger company system.

This repository owns the Marketing Content Generator component.

The product depends on a shared data contract so that all Riverside Books products can work with consistent book information, including fields such as:

- Book ID
- Title
- Author
- Genre
- Price
- Stock Status
- Description
- Rating
- Promotional Tags

Maintaining consistent data structures allows each product to communicate reliably when the complete Riverside Books platform is assembled.

## Current Goal

The current goal is to build a reliable marketing content generation system that can:

1. Accept structured book data.
2. Generate useful marketing outputs.
3. Select a timely reader-engagement action from reader and community signals.
4. Handle realistic data variations and edge cases.
5. Provide a foundation for future AI-powered marketing workflows.

## Reader-engagement MVP

The existing catalog-only `POST /generate` request remains supported. Callers can
also send an object with `catalog` and an optional `reader_context`:

```json
{
  "catalog": [{ "book_id": "RB-001", "title": "..." }],
  "reader_context": {
    "reader_id": "reader-7",
    "favorite_genres": ["Science Fiction"],
    "books_read": ["RB-001"],
    "active_challenge": "Riverside Discovery Trail",
    "challenge_progress": 65,
    "last_visit": "2026-08-01"
  }
}
```

The response keeps `generated_drafts` for compatibility and adds one
`engagement_messages` item when reader context is supplied. Each item contains
`message_type`, `reader_or_segment`, `recommended_book`, `reason_selected`,
`headline`, `body_copy`, and `call_to_action`. Current decision types are
`challenge_completion_nudge`, `genre_exploration_quest`,
`personalized_discovery`, `comeback_challenge`, and `community_progress`.

`challenge_progress` and `community_progress` are percentages from 0 to 100;
`books_read` contains catalog `book_id` values. Reader context is validated
separately from the existing nine-field book contract. See
`data/reader-context.schema.json` for the shared shape.

## Project Structure

```
riverside-marketing-content-generator/

├── README.md
├── docs/
├── data/
├── src/
└── tests/
```

## Development Approach

This project follows an AI-native engineering workflow:

- Define the product requirements first.
- Establish a clear data contract.
- Build and test core functionality.
- Add AI capabilities with controlled inputs and outputs.
- Document decisions and lessons learned.

## Status

🚧 In Development

Product D: Marketing Content Generator
