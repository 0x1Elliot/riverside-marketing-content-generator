# Tests

Tests will be organized around the product boundaries and the shared data contract.

Current coverage includes:

- valid sample and marketing edge-case book records;
- invalid records from the contract fixtures;
- safe partitioning of valid and invalid collection entries;
- rejection of unknown fields and malformed collection files;
- deterministic promotional, social, and email marketing drafts;
- structured draft fields, source context, content-type handling, and input ordering;
- all-valid, mixed, and all-invalid catalog orchestration;
- rejected-record diagnostics and generation isolation for invalid records.
- CLI success, fatal file errors, rejected-record output, and stable JSON serialization.
- HTTP health, generation, malformed-request, deterministic-response, and validation-success behavior.
- reader-context validation, all five engagement decisions, structured engagement output, and frontend request-shape helpers.

External AI generation, APIs, channel publishing, and review workflows are not tested because they have not been implemented.

Run the suite with:

```bash
python3 -m unittest discover -s tests -v
```
