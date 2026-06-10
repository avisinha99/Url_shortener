# Write-up

## 1. What I asked the AI to do, and what I decided myself

I drove the build in small, reviewable steps and used the AI to scaffold and implement each one after I had decided the design.

I decided myself:

- The overall stack (FastAPI + SQLAlchemy + SQLite) and that the build should be committed incrementally, one feature per commit, rather than in a single dump.
- The data model: a single `links` table with a `UNIQUE` code, an indexed `original_url`, and an `is_custom` flag to separate auto codes from user aliases.
- The behavioural rules: idempotent duplicate handling, alias conflict semantics (`409`), reserved aliases, and `301` (not `302`) for redirects.
- The short-code strategy: random base62 with a DB uniqueness guarantee, rather than sequential IDs or hashing.

I asked the AI to:

- Scaffold the project structure and dependencies.
- Implement each layer once I specified its responsibility: config/db/models, validators, code generator, the shorten service, the routes, and the tests.
- Write the validation rules and the idempotency/alias branching to my spec, then verify each step by running it.

## 2. Where I overrode, corrected, or threw away the AI's output

- **URL field type.** The first version used Pydantic's `HttpUrl`, which made invalid URLs return `422`. I changed `url` to a plain `str` so my own `normalize_url()` owns all URL rules and returns a consistent `400` with a clear message. This keeps validation logic in one place.
- **Scope discipline.** An early pass generated the entire app at once. I threw that away and rebuilt it step by step so the commit history reflects how it came together.
- **URL normalization.** I kept normalization limited to lowercasing the scheme and host. Lowercasing the whole URL would have been wrong because paths and query strings can be case-sensitive.
- **Service structure.** I split the shorten service into focused helpers (`_shorten_with_generated_code`, `_shorten_with_alias`) instead of one long function, to make the two code paths obvious and testable.

## 3. Biggest trade-offs and alternatives considered

1. **Idempotent duplicates vs. always-new codes.** I chose to return the existing code for a repeated URL. This keeps the table small and behaviour predictable, at the cost of not supporting multiple short links for the same destination (e.g. per-campaign links). The alternative (always mint a new code) is better for analytics but adds clutter; I'd revisit it if tracking were a requirement.

2. **Random base62 + DB uniqueness vs. sequential IDs.** Random 7-char codes don't leak how many links exist and are trivially URL-safe. The cost is needing a uniqueness check and a retry loop. Sequential base62 of an auto-increment ID would never collide and needs no retries, but exposes volume and ordering. The `UNIQUE` constraint is the real collision guarantee either way.

3. **SQLite vs. Postgres.** SQLite needs zero setup and is perfect for a take-home and the live session. It won't handle real concurrent write load, and the collision retry relies on the DB raising an integrity error. The `DATABASE_URL` setting means swapping to Postgres later is mostly configuration.

## 4. What's missing, or what I'd do with another day

- **Click analytics.** The exercise title mentions analytics; I'd add a `clicks` table and record a row (or increment a counter) on each redirect, plus a `GET /{code}/stats` endpoint.
- **Link expiration / TTL** and soft deletes.
- **Rate limiting and abuse protection** on `POST /shorten`.
- **Postgres migration + Alembic** for real schema management instead of `create_all`.
- **Observability**: structured logging and basic metrics.
- **A redirect cache** (e.g. Redis) for hot codes to take read load off the database.
