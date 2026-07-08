# Redis Design

## Redis Key Naming Convention
Pattern: '{feature}:{identifier}:{attribute}'
Examples:
    - 'link:slug:abc123' -  stores cached link data for slug "abc123"
    - 'clicks:stream' - stores click event in Redis stream
    - 'rate:api_key:xyz789' - stores rate limit counters for API keys


## Link Cache Key Design
    - Key pattern: 'link:slug:{slug}' - where {slug} is the acutal slug e.g. "abc123"
    - Data Type: Redis Hash - like a dictionary with multiple fields
    - Hash fields to store:
        - 'original_url'
        - 'expires_at' (if applicable)
        - 'password_hash' (if link is password protected)
        - 'is_deleted' (soft delete boolean)
    - TTL (Time To Live): 3600 seconds (1 hour) for most links
    - For links with expiration: set TTL to match the link's expiration time minus 5 min

## Click Buffer Key Design
    - Key pattern: 'clicks:stream' (single key for all clicks)
    - Data type: Redis Stream 
    - Each entry in the stream contains:
        - 'link_id'
        - 'clicked_at'
        - 'country_code'
        - 'referrer' (what website referred the click)
        - 'device_type' (mobile, desktop, etc)
        - 'user_agent' (the browsers user agent string)
    - TTL: 86400 seconds (24 hours) - old entries are automatically removed

## Rate Limiting Key Design
    - Key pattern: 'rate:api_key:{api_key}' - where {api_key} is the actual API key
    - Data Type: Redis Hash - like a dictionary with multiple fields
    - Hash fields to store:
        - 'requests_count' - number of requests made
        - 'last_reset_at' - timestamp of last reset
    - TTL (Time To Live): 3600 seconds (1 hour) for most API keys
    - For API keys with different rate limits: set TTL to match the rate limit period

## Analytics Cache Key Design
    - Key pattern: 'stats:link:{slug}:{period}' - where {slug} is the actual slug and {period} is the time period (e.g. "1day", "7days", "30days")
    - Data Type: Redis Hash - like a dictionary with multiple fields
    - Hash fields to store:
        - 'total_clicks' - total number of clicks
        - 'clicks_by_day' - clicks broken down by day (as JSON)
        - 'top_countries' - top 10 countries (as JSON)
        - 'top_referrers' - top 10 referring websites (as JSON)
        - 'devices' - breakdown by device type (as JSON)
    - TTL (Time To Live): 300 seconds (5 minutes) - analytics can be slightly stale

## Cache Invalidation Strategy
    - When a link is updated: delete `link:slug:{slug}` from Redis
    - When a link is deleted: delete `link:slug:{slug}` from Redis immediately
    - When a link expires: let the TTL expire naturally (no manual deletion needed)
    - For analytics cache: let TTL expire naturally (5 minutes)

## All Keys Summary
| Key Pattern | Data Type | TTL | Purpose |
|-------------|-----------|-----|---------|
| `link:slug:{slug}` | Hash | 3600s | Cache link data for fast redirects |
| `clicks:stream` | Stream | 86400s | Buffer click events before DB write |
| `rate:api_key:{hash}:{window}` | String | 60s/3600s | Rate limiting per API key |
| `stats:link:{slug}:{period}` | Hash | 300s | Cache analytics queries |


