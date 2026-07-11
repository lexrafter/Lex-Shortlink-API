# Index Plan

## links

| Column | Index type | Reason |
|--------|-----------|--------|
| `slug` | UNIQUE | Every redirect does `WHERE slug = ?` — this is the hottest query in the whole system |
| `api_key_id` | Plain | Filtering links by who created them |
| `expires_at` | Plain | Filtering out expired links efficiently |
| `is_deleted` | — | Low cardinality (only true/false), not worth indexing alone |

## click_events

| Column | Index type | Reason |
|--------|-----------|--------|
| `link_id` | Plain | Every analytics query filters by link — `WHERE link_id = ?` |
| `clicked_at` | Plain | Aggregating clicks over time — `WHERE clicked_at > now() - interval '7 days'` |
| `(link_id, clicked_at)` | Composite | Covers the most common analytics query: clicks for a link over a time range |

## api_keys

| Column | Index type | Reason |
|--------|-----------|--------|
| `key_hash` | UNIQUE | Auth middleware does `WHERE key_hash = ?` on every request |