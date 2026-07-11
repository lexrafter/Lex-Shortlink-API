##Caching

##The Problem:
Need to handle 10,000 redirects per second with very low latency (fast response times). Querying the database for every redirect would be too slow.

##The Solution:
Use a "read-through cache" pattern. This means: when someone requests a link, we check Redis first. If the data is there (cache hit), we return it immediately. If not (cache miss), we get it from the database and store it in cache (Redis) for next time.

##Pros:
- Very fast redirects when data is cached
- Reduces load on the database
- Cache fills up automatically as people use the system

##Cons:
- Cached data might be stale (outdated)
- Need a strategy to update/delete cached data when it changes (potentially a daemon function?)

##Async Click Logging

##The Problem:
When someone clicks a link, we need to record that click in the database. But if we write to the database immediately during the redirect, it will slow down the redirect. We want redirects to be as fast as possible.

##The Solution:
Use "async click logging." When a click happens, we quickly write it to Redis (which is very fast) and immediately return the redirect. A separate background worker process reads from Redis and writes to the database later.

##Pros:
- Redirects are not blocked by database writes
- Database writes happen in batches (more efficient)
- Can handle traffic spikes (Redis handles high throughput better than database)

##Cons:
- Analytics are not instantly up-to-date (eventual consistency)
- Need to run a separate worker process
- Risk of losing clicks if worker crashes before processing

##Read Through Cache Flow
```
    User Request → Check Redis → Cache Hit? → Yes: Return Data
                                        → No: Get from DB → Store in Redis → Return Data
    ```
##Async Click Logging Flow
```
    User Clicks Link → Write to Redis Stream → Return Redirect Immediately
                                          ↓
                                    Background Worker Reads Stream
                                          ↓
                                    Worker Writes to Database
    ```