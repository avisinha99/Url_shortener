# Write-up

## 1. What I asked the AI to do, and what I decided myself

I drove the build in small, reviewable steps and used the AI to scaffold and implement each one after I had decided the design.

I decided myself:

- The overall stack (FastAPI + SQLAlchemy + SQLite) and that the build should be committed incrementally, one feature per commit.
- The data model: a `links` table with a `UNIQUE` code, an indexed `original_url`, and an `is_custom` flag; plus a `clicks` table (one row per redirect) for analytics.
- The behavioural rules: idempotent duplicate handling, alias conflict semantics (`409`), reserved aliases, and `301` (not `302`) for redirects.
- The short-code strategy: random base62 with a DB uniqueness guarantee, rather than sequential IDs or hashing.
- The analytics approach: record a click row on each successful redirect and expose stats via `GET /{code}/stats`, rather than a simple counter column (so `last_clicked_at` and future breakdowns are possible).

I asked the AI to:

- Scaffold the project structure and dependencies.
- Implement each layer once I specified its responsibility: config/db/models, validators, code generator, the shorten service, the routes, tests, and click analytics.
- Write the validation rules and the idempotency/alias branching to my spec, then verify each step by running it.

## 2. Where I overrode, corrected, or threw away the AI's output

- **URL field type.** The first version used Pydantic's `HttpUrl`, which made invalid URLs return `422`. I changed `url` to a plain `str` so my own `normalize_url()` owns all URL rules and returns a consistent `400` with a clear message. This keeps validation logic in one place.
- **URL normalization.** I kept normalization limited to lowercasing the scheme and host. Lowercasing the whole URL would have been wrong because paths and query strings can be case-sensitive.
- **Service structure.** I split the shorten service into focused helpers (`_shorten_with_generated_code`, `_shorten_with_alias`) instead of one long function, to make the two code paths obvious and testable.
- **Analytics storage.** I chose one row per click in a `clicks` table instead of a counter on `links`. Slightly more storage, but it gives accurate `last_clicked_at` and leaves room for richer reporting later.

## 3. Biggest trade-offs and alternatives considered

1. **Idempotent duplicates vs. always-new codes.** I still return the existing auto-generated code when the same URL is shortened again. That keeps the table small and behaviour predictable. Click analytics is tracked **per short code** (via the `clicks` table), not per original URL — so repeated shorten requests for the same URL share one code and one click stream. If you need multiple trackable links to the same destination (e.g. separate campaign codes), the supported path today is **custom aliases**; the alternative of always minting a new auto code on every request would enable that without aliases but would grow the `links` table faster.

2. **Random base62 + DB uniqueness vs. sequential IDs.** Random 7-char codes don't leak how many links exist and are trivially URL-safe. The cost is needing a uniqueness check and a retry loop. Sequential base62 of an auto-increment ID would never collide and needs no retries, but exposes volume and ordering. The `UNIQUE` constraint is the real collision guarantee either way.

3. **SQLite vs. Postgres.** SQLite needs zero setup and is perfect for a take-home and the live session. It won't handle real concurrent write load, and the collision retry relies on the DB raising an integrity error. The `DATABASE_URL` setting means swapping to Postgres later is mostly configuration.

## 4. What's missing, or what I'd do with another day

- **Per-campaign auto codes for the same URL** without requiring custom aliases (would mean dropping idempotency or making it optional).
- **Richer analytics**: clicks by day, referrer, or user-agent.
- **Link expiration / TTL** and soft deletes.
- **Rate limiting and abuse protection** on `POST /shorten`.
- **Postgres migration + Alembic** for real schema management instead of `create_all`.
- **Observability**: structured logging and basic metrics.
- **A redirect cache** (e.g. Redis) for hot codes to take read load off the database.
