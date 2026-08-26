# Product D — Marketing Content Generator

Primary product area for Riverside Books.

## Purpose

Create reviewable marketing drafts from structured book and campaign information.

## First candidate use cases

- Launch copy for a new or featured book.
- Social post variations for a campaign.
- Email copy for a curated recommendation or promotion.
- Short product-description drafts based on approved book details.
- Reader-engagement messages based on optional reader and community context.

## Product requirements to validate

- Required inputs and supported content formats.
- Riverside Books brand voice and reusable guidance.
- Source attribution and protection against unsupported claims.
- Draft review, editing, approval, and export or publishing handoff.

## Definition of a useful first slice

A bookstore team member can provide a small set of approved inputs, generate a draft for one channel, edit it, and understand which details came from the source material.

The current engagement MVP preserves that catalog-only workflow and additionally
accepts `reader_context` with fields such as `reader_id`, `favorite_genres`,
`books_read`, `active_challenge`, `challenge_progress`, and `last_visit`. It
selects a structured next-best message for challenge completion, exploration,
discovery, comeback, or community progress.
