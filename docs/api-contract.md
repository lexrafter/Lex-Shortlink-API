# API Contract

Base path: `/api/v1`

---

## POST /api/v1/links

Shorten a URL.

**Request body**
```json
{
  "url": "https://example.com/some/long/path",
  "custom_slug": "my-link",   // optional
  "expires_at": "2026-12-31T00:00:00Z",  // optional
  "password": "secret"        // optional
}
```

**Responses**

| Status | Meaning |
|--------|---------|
| 201 | Created — returns the short link |
| 400 | Invalid URL or bad input |
| 409 | Custom slug already taken |
| 422 | Validation error (malformed body) |
| 429 | Rate limit exceeded |

**Response body (201)**
```json
{
  "slug": "my-link",
  "short_url": "http://localhost:8000/my-link",
  "url": "https://example.com/some/long/path",
  "expires_at": "2026-12-31T00:00:00Z",
  "created_at": "2026-06-16T10:00:00Z"
}
```

---

## GET /{slug}

Redirect to the original URL.

**Responses**

| Status | Meaning |
|--------|---------|
| 302 | Found — redirects to original URL |
| 404 | Slug not found |
| 410 | Link expired or deleted |

---

## GET /api/v1/links/{slug}/stats

Return click analytics for a link.

**Responses**

| Status | Meaning |
|--------|---------|
| 200 | Returns analytics data |
| 404 | Slug not found |

**Response body (200)**
```json
{
  "slug": "my-link",
  "total_clicks": 142,
  "clicks_by_day": [
    { "date": "2026-06-15", "clicks": 80 },
    { "date": "2026-06-16", "clicks": 62 }
  ],
  "top_countries": [
    { "country_code": "AU", "clicks": 90 }
  ],
  "top_referrers": [
    { "referrer": "https://twitter.com", "clicks": 50 }
  ],
  "devices": {
    "desktop": 100,
    "mobile": 42
  }
}
```

---

## GET /health

Health check.

**Responses**

| Status | Meaning |
|--------|---------|
| 200 | API is up |