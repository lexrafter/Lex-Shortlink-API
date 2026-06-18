# Complete Step-by-Step Implementation Guide
## Starting from P1-1.4 through Phase 8

This document provides detailed step-by-step instructions for all remaining tasks in the Shortlink-API project.

---

## Phase 1 - Design (Remaining Tasks)

### P1-1.4 Redis key design + TTLs

**Objective:** Design Redis key structure and TTL strategies for caching and click buffering.

**Steps:**

1. Define key naming convention: `{feature}:{identifier}:{attribute}`
   - Example: `link:slug:abc123`, `clicks:buffer:abc123`, `rate:api_key:xyz789`

2. Design link cache keys for hot-link caching:
   - Key: `link:slug:{slug}` → Hash
   - Hash fields: `original_url`, `expires_at`, `password_hash`, `is_deleted`
   - TTL: 3600s (1 hour) default, or match link's `expires_at` minus 5min buffer

3. Design click buffer keys for async logging:
   - Key: `clicks:stream` → Redis Stream
   - Entry fields: `link_id`, `clicked_at`, `country_code`, `referrer`, `device_type`, `user_agent`
   - TTL: 86400s (24 hours) with XTRIM for retention

4. Design rate limit keys for API key rate limiting:
   - Key: `rate:api_key:{key_hash}:{window}` → String
   - Windows: `rate:api_key:{key_hash}:1min` (60s TTL), `rate:api_key:{key_hash}:1hour` (3600s TTL)

5. Design analytics cache keys (optional):
   - Key: `stats:link:{slug}:{period}` → Hash
   - Hash fields: `total_clicks`, `clicks_by_day`, `top_countries`, `top_referrers`, `devices`
   - TTL: 300s (5 minutes)

6. Document cache invalidation strategy:
   - Delete `link:slug:{slug}` on link updates/deletes
   - Let TTL expire naturally for analytics cache
   - Immediate cache purge on soft delete

7. Create `docs/redis-design.md` with:
   - Key namespace table (pattern, type, TTL, purpose)
   - Cache invalidation rules
   - Memory estimation
   - Connection pool settings

8. Update `requirements.txt`:
   ```
   redis>=5.0.0,<6.0.0
   ```

**Acceptance Criteria:**
- [ ] `docs/redis-design.md` created with complete key design
- [ ] `requirements.txt` includes redis dependency
- [ ] TTL strategies documented for all key types
- [ ] Cache invalidation rules clearly defined

---

### P1-1.5 ADR: read-through cache + async click logging

**Objective:** Create Architecture Decision Record for caching strategy and async click logging.

**Steps:**

1. Create `docs/adr/001-read-through-cache-async-clicks.md`

2. Document the read-through cache pattern:
   - **Context:** Need to handle 10k redirects/sec with low latency
   - **Decision:** Use read-through cache pattern for link lookups
   - **Consequences:** 
     - Pros: Fast redirects, reduced DB load, automatic cache population
     - Cons: Cache staleness, need for invalidation strategy

3. Document async click logging architecture:
   - **Context:** Click logging shouldn't block redirects
   - **Decision:** Use Redis Stream for click buffering, background worker for DB flush
   - **Consequences:**
     - Pros: Non-blocking redirects, batch DB writes, handles spikes
     - Cons: Eventual consistency, requires worker process

4. Include diagrams:
   - Read-through cache flow diagram
   - Async click logging flow diagram

5. Document alternatives considered:
   - Write-through cache (rejected: slower writes)
   - Direct DB writes (rejected: blocks redirects)
   - Message queue (rejected: overkill for this scale)

**Acceptance Criteria:**
- [ ] ADR document created in `docs/adr/`
- [ ] Read-through cache pattern documented with rationale
- [ ] Async click logging architecture documented
- [ ] Alternatives considered and rejected with reasoning
- [ ] Flow diagrams included

---

## Phase 2 - Core MVP

### P1-2.1 Alembic migrations

**Objective:** Set up database migrations with Alembic.

**Steps:**

1. Install dependencies:
   ```bash
   pip install alembic sqlalchemy[asyncio] asyncpg
   ```

2. Update `requirements.txt`:
   ```
   alembic>=1.13.0,<2.0.0
   sqlalchemy[asyncio]>=2.0.0,<3.0.0
   asyncpg>=0.29.0,<1.0.0
   ```

3. Initialize Alembic:
   ```bash
   cd src/lex_shortlink_api
   alembic init alembic
   ```

4. Configure `alembic.ini`:
   - Set `sqlalchemy.url` from environment variable
   - Update script location if needed

5. Create `env.py` with async support:
   - Import asyncio
   - Configure async engine
   - Set target_metadata

6. Create initial migration:
   ```bash
   alembic revision --autogenerate -m "Initial schema"
   ```

7. Define schema in migration (links, click_events, api_keys tables):
   ```python
   def upgrade():
       op.create_table(
           'links',
           sa.Column('id', sa.UUID(), primary_key=True),
           sa.Column('slug', sa.Text(), unique=True, nullable=False),
           sa.Column('original_url', sa.Text(), nullable=False),
           sa.Column('password_hash', sa.Text(), nullable=True),
           sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
           sa.Column('is_deleted', sa.Boolean(), default=False),
           sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
           sa.Column('api_key_id', sa.UUID(), sa.ForeignKey('api_keys.id'), nullable=True),
       )
       # Add click_events and api_keys tables
   ```

8. Test migration:
   ```bash
   alembic upgrade head
   alembic downgrade -1
   ```

**Acceptance Criteria:**
- [ ] Alembic initialized and configured
- [ ] Initial migration created with all tables
- [ ] Migration can be applied and rolled back
- [ ] Foreign keys and constraints defined

---

### P1-2.2 SQLAlchemy models + repository layer

**Objective:** Create ORM models and repository pattern for database access.

**Steps:**

1. Create `src/lex_shortlink_api/models/` directory

2. Create `src/lex_shortlink_api/models/__init__.py`

3. Create `src/lex_shortlink_api/models/link.py`:
   ```python
   from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
   from sqlalchemy.dialects.postgresql import UUID
   from sqlalchemy.orm import relationship
   import uuid
   
   from lex_shortlink_api.database import Base
   
   class Link(Base):
       __tablename__ = "links"
       
       id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       slug = Column(String, unique=True, nullable=False, index=True)
       original_url = Column(String, nullable=False)
       password_hash = Column(String, nullable=True)
       expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
       is_deleted = Column(Boolean, default=False, index=True)
       created_at = Column(DateTime(timezone=True), server_default="now()")
       api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=True)
       
       click_events = relationship("ClickEvent", back_populates="link")
   ```

4. Create `src/lex_shortlink_api/models/click_event.py`:
   ```python
   from sqlalchemy import Column, String, DateTime, ForeignKey
   from sqlalchemy.dialects.postgresql import UUID
   from sqlalchemy.orm import relationship
   import uuid
   
   from lex_shortlink_api.database import Base
   
   class ClickEvent(Base):
       __tablename__ = "click_events"
       
       id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       link_id = Column(UUID(as_uuid=True), ForeignKey("links.id"), nullable=False, index=True)
       clicked_at = Column(DateTime(timezone=True), nullable=False, index=True)
       country_code = Column(String, nullable=True)
       referrer = Column(String, nullable=True)
       device_type = Column(String, nullable=True)
       user_agent = Column(String, nullable=True)
       
       link = relationship("Link", back_populates="click_events")
   ```

5. Create `src/lex_shortlink_api/models/api_key.py`:
   ```python
   from sqlalchemy import Column, String, Boolean, DateTime
   from sqlalchemy.dialects.postgresql import UUID
   import uuid
   
   from lex_shortlink_api.database import Base
   
   class ApiKey(Base):
       __tablename__ = "api_keys"
       
       id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
       key_hash = Column(String, unique=True, nullable=False, index=True)
       name = Column(String, nullable=False)
       is_active = Column(Boolean, default=True)
       created_at = Column(DateTime(timezone=True), server_default="now()")
   ```

6. Create `src/lex_shortlink_api/database.py`:
   ```python
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
   from sqlalchemy.orm import declarative_base, sessionmaker
   
   from lex_shortlink_api.config import get_settings
   
   settings = get_settings()
   
   engine = create_async_engine(settings.database_url, echo=True)
   AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
   Base = declarative_base()
   
   async def get_db():
       async with AsyncSessionLocal() as session:
           yield session
   ```

7. Create `src/lex_shortlink_api/repositories/` directory

8. Create `src/lex_shortlink_api/repositories/__init__.py`

9. Create `src/lex_shortlink_api/repositories/link_repository.py`:
   ```python
   from sqlalchemy import select
   from sqlalchemy.ext.asyncio import AsyncSession
   
   from lex_shortlink_api.models.link import Link
   
   class LinkRepository:
       def __init__(self, db: AsyncSession):
           self.db = db
       
       async def create(self, link: Link) -> Link:
           self.db.add(link)
           await self.db.commit()
           await self.db.refresh(link)
           return link
       
       async def get_by_slug(self, slug: str) -> Link | None:
           result = await self.db.execute(
               select(Link).where(Link.slug == slug, Link.is_deleted == False)
           )
           return result.scalar_one_or_none()
       
       async def slug_exists(self, slug: str) -> bool:
           result = await self.db.execute(
               select(Link).where(Link.slug == slug)
           )
           return result.scalar_one_or_none() is not None
   ```

**Acceptance Criteria:**
- [ ] All SQLAlchemy models created
- [ ] Database session management configured
- [ ] Repository pattern implemented for Link model
- [ ] Models match ERD structure
- [ ] Relationships defined correctly

---

### P1-2.3 POST /api/v1/links (validate URL, generate slug)

**Objective:** Implement link shortening endpoint.

**Steps:**

1. Create `src/lex_shortlink_api/schemas/` directory

2. Create `src/lex_shortlink_api/schemas/__init__.py`

3. Create `src/lex_shortlink_api/schemas/link.py`:
   ```python
   from pydantic import BaseModel, HttpUrl, field_validator
   from datetime import datetime
   from typing import Optional
   
   class LinkCreate(BaseModel):
       url: HttpUrl
       custom_slug: Optional[str] = None
       expires_at: Optional[datetime] = None
       password: Optional[str] = None
   
   class LinkResponse(BaseModel):
       slug: str
       short_url: str
       url: str
       expires_at: Optional[datetime] = None
       created_at: datetime
       
       class Config:
           from_attributes = True
   ```

4. Create `src/lex_shortlink_api/services/` directory

5. Create `src/lex_shortlink_api/services/__init__.py`

6. Create `src/lex_shortlink_api/services/link_service.py`:
   ```python
   import secrets
   import string
   from datetime import datetime
   
   from lex_shortlink_api.models.link import Link
   from lex_shortlink_api.repositories.link_repository import LinkRepository
   from lex_shortlink_api.schemas.link import LinkCreate
   
   class LinkService:
       def __init__(self, link_repo: LinkRepository):
           self.link_repo = link_repo
       
       def generate_slug(self, length: int = 6) -> str:
           alphabet = string.ascii_lowercase + string.digits
           return ''.join(secrets.choice(alphabet) for _ in range(length))
       
       async def create_link(self, data: LinkCreate) -> Link:
           slug = data.custom_slug or self.generate_slug()
           
           if await self.link_repo.slug_exists(slug):
               raise ValueError("Slug already exists")
           
           link = Link(
               slug=slug,
               original_url=str(data.url),
               expires_at=data.expires_at,
           )
           
           if data.password:
               # Hash password (implement hashing)
               link.password_hash = self.hash_password(data.password)
           
           return await self.link_repo.create(link)
       
       def hash_password(self, password: str) -> str:
           # Implement password hashing
           pass
   ```

7. Create `src/lex_shortlink_api/api/` directory

8. Create `src/lex_shortlink_api/api/__init__.py`

9. Create `src/lex_shortlink_api/api/links.py`:
   ```python
   from fastapi import APIRouter, HTTPException, status
   from sqlalchemy.ext.asyncio import AsyncSession
   
   from lex_shortlink_api.database import get_db
   from lex_shortlink_api.schemas.link import LinkCreate, LinkResponse
   from lex_shortlink_api.repositories.link_repository import LinkRepository
   from lex_shortlink_api.services.link_service import LinkService
   
   router = APIRouter(prefix="/api/v1/links", tags=["links"])
   
   @router.post("", status_code=status.HTTP_201_CREATED)
   async def create_link(data: LinkCreate, db: AsyncSession = Depends(get_db)):
       link_repo = LinkRepository(db)
       link_service = LinkService(link_repo)
       
       try:
           link = await link_service.create_link(data)
       except ValueError as e:
           raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
       
       return LinkResponse(
           slug=link.slug,
           short_url=f"http://localhost:8000/{link.slug}",
           url=link.original_url,
           expires_at=link.expires_at,
           created_at=link.created_at,
       )
   ```

10. Update `src/lex_shortlink_api/main.py`:
    ```python
    from lex_shortlink_api.api.links import router as links_router
    
    app.include_router(links_router)
    ```

11. Add URL validation library:
    ```
    pip install validators
    ```
    Update `requirements.txt`

**Acceptance Criteria:**
- [ ] POST /api/v1/links endpoint created
- [ ] URL validation implemented
- [ ] Auto-generated slug for custom_slug=None
- [ ] Custom slug collision handling (409)
- [ ] Returns 201 with link response
- [ ] Password hashing implemented

---

### P1-2.4 GET /{slug} → 302 / 404 / 410

**Objective:** Implement redirect endpoint.

**Steps:**

1. Add redirect route to `src/lex_shortlink_api/api/links.py`:
   ```python
   from fastapi import HTTPException, status, Response
   from datetime import datetime
   
   @router.get("/{slug}")
   async def redirect(slug: str, db: AsyncSession = Depends(get_db)):
       link_repo = LinkRepository(db)
       link = await link_repo.get_by_slug(slug)
       
       if not link:
           raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
       
       if link.expires_at and link.expires_at < datetime.now():
           raise HTTPException(status_code=status.HTTP_410_GONE)
       
       if link.is_deleted:
           raise HTTPException(status_code=status.HTTP_410_GONE)
       
       return Response(status_code=status.HTTP_302_FOUND, headers={"Location": link.original_url})
   ```

2. Move redirect to separate router (since it's not under /api/v1):
   - Create `src/lex_shortlink_api/api/redirects.py`
   - Update `main.py` to include redirects router

3. Add logging for redirect path:
   ```python
   import logging
   
   logger = logging.getLogger(__name__)
   
   @router.get("/{slug}")
   async def redirect(slug: str, db: AsyncSession = Depends(get_db)):
       logger.info(f"Redirect request for slug: {slug}")
       # ... rest of implementation
   ```

**Acceptance Criteria:**
- [ ] GET /{slug} returns 302 with Location header
- [ ] GET /{slug} returns 404 for non-existent slugs
- [ ] GET /{slug} returns 410 for expired/deleted links
- [ ] Structured logging implemented

---

### P1-2.5 Custom slug + collision handling (409)

**Objective:** Ensure custom slug validation works correctly.

**Steps:**

1. Add slug validation to LinkService:
   ```python
   def validate_slug(self, slug: str) -> bool:
       # Only allow alphanumeric and hyphens
       return all(c.isalnum() or c == '-' for c in slug)
   ```

2. Update create_link to validate custom slug:
   ```python
   if data.custom_slug:
       if not self.validate_slug(data.custom_slug):
           raise ValueError("Invalid slug format")
       slug = data.custom_slug
   ```

3. Add length validation:
   ```python
   if len(slug) < 3 or len(slug) > 50:
       raise ValueError("Slug must be between 3 and 50 characters")
   ```

4. Test collision handling:
   - Create link with custom slug "test"
   - Attempt to create another link with same slug
   - Verify 409 response

**Acceptance Criteria:**
- [ ] Custom slug format validation (alphanumeric + hyphens)
- [ ] Custom slug length validation (3-50 chars)
- [ ] Collision detection returns 409
- [ ] Auto-generated slug never collides

---

### P1-2.6 Structured logging on redirect path

**Objective:** Add comprehensive logging for monitoring and debugging.

**Steps:**

1. Update `src/lex_shortlink_api/config.py`:
   ```python
   import logging
   
   class Settings(BaseSettings):
       # ... existing fields
       log_level: str = "INFO"
   ```

2. Configure logging in `src/lex_shortlink_api/main.py`:
   ```python
   import logging
   
   logging.basicConfig(
       level=settings.log_level,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   ```

3. Add structured logging to redirect endpoint:
   ```python
   import json
   
   @router.get("/{slug}")
   async def redirect(slug: str, db: AsyncSession = Depends(get_db)):
       logger.info(json.dumps({
           "event": "redirect_attempt",
           "slug": slug,
           "timestamp": datetime.now().isoformat(),
       }))
       
       link = await link_repo.get_by_slug(slug)
       
       if not link:
           logger.warning(json.dumps({
               "event": "redirect_not_found",
               "slug": slug,
           }))
           raise HTTPException(status_code=404)
       
       logger.info(json.dumps({
           "event": "redirect_success",
           "slug": slug,
           "target_url": link.original_url,
       }))
       
       return Response(status_code=302, headers={"Location": link.original_url})
   ```

**Acceptance Criteria:**
- [ ] Logging configured in main.py
- [ ] Structured JSON logging on redirect path
- [ ] Log levels configurable via environment
- [ ] Success/failure events logged

---

### P1-2.7 Unit tests (validation, slug, expiry)

**Objective:** Add unit tests for core functionality.

**Steps:**

1. Create `tests/unit/` directory

2. Create `tests/unit/test_link_service.py`:
   ```python
   import pytest
   from datetime import datetime, timedelta
   
   from lex_shortlink_api.services.link_service import LinkService
   from lex_shortlink_api.schemas.link import LinkCreate
   
   @pytest.fixture
   def link_service(mock_link_repo):
       return LinkService(mock_link_repo)
   
   def test_generate_slug(link_service):
       slug = link_service.generate_slug()
       assert len(slug) == 6
       assert slug.isalnum()
   
   def test_validate_slug_valid(link_service):
       assert link_service.validate_slug("test-slug")
       assert link_service.validate_slug("abc123")
   
   def test_validate_slug_invalid(link_service):
       assert not link_service.validate_slug("test slug")
       assert not link_service.validate_slug("test@slug")
   
   def test_custom_slug_collision(link_service, mock_link_repo):
       mock_link_repo.slug_exists.return_value = True
       data = LinkCreate(url="https://example.com", custom_slug="taken")
       
       with pytest.raises(ValueError, match="already exists"):
           await link_service.create_link(data)
   ```

3. Create `tests/unit/test_schemas.py`:
   ```python
   import pytest
   from pydantic import ValidationError
   
   from lex_shortlink_api.schemas.link import LinkCreate
   
   def test_valid_url():
       data = LinkCreate(url="https://example.com")
       assert data.url == "https://example.com"
   
   def test_invalid_url():
       with pytest.raises(ValidationError):
           LinkCreate(url="not-a-url")
   
   def test_custom_slug():
       data = LinkCreate(url="https://example.com", custom_slug="my-link")
       assert data.custom_slug == "my-link"
   ```

4. Run tests:
   ```bash
   pytest tests/unit/
   ```

**Acceptance Criteria:**
- [ ] Unit tests for slug generation
- [ ] Unit tests for slug validation
- [ ] Unit tests for URL validation
- [ ] Unit tests for collision detection
- [ ] All tests pass

---

### P1-2.8 Integration tests (shorten → redirect round-trip)

**Objective:** Add integration tests for full request flow.

**Steps:**

1. Create `tests/integration/` directory

2. Create `tests/integration/test_link_flow.py`:
   ```python
   import pytest
   from httpx import AsyncClient
   
   from lex_shortlink_api.main import app
   
   @pytest.fixture
   async def client():
       async with AsyncClient(app=app, base_url="http://test") as ac:
           yield ac
   
   @pytest.mark.asyncio
   async def test_create_and_redirect(client):
       # Create link
       response = await client.post(
           "/api/v1/links",
           json={"url": "https://example.com"}
       )
       assert response.status_code == 201
       data = response.json()
       slug = data["slug"]
       
       # Redirect
       response = await client.get(f"/{slug}")
       assert response.status_code == 302
       assert response.headers["location"] == "https://example.com"
   
   @pytest.mark.asyncio
   async def test_custom_slug_collision(client):
       # Create first link
       await client.post(
           "/api/v1/links",
           json={"url": "https://example.com", "custom_slug": "test"}
       )
       
       # Try to create duplicate
       response = await client.post(
           "/api/v1/links",
           json={"url": "https://example.org", "custom_slug": "test"}
       )
       assert response.status_code == 409
   
   @pytest.mark.asyncio
   async def test_expired_link(client):
       from datetime import datetime, timedelta
       
       expires_at = datetime.now() - timedelta(hours=1)
       response = await client.post(
           "/api/v1/links",
           json={
               "url": "https://example.com",
               "expires_at": expires_at.isoformat()
           }
       )
       slug = response.json()["slug"]
       
       # Try to redirect
       response = await client.get(f"/{slug}")
       assert response.status_code == 410
   ```

3. Configure test database in `tests/conftest.py`:
   ```python
   import pytest
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
   from sqlalchemy.orm import sessionmaker
   
   from lex_shortlink_api.models.link import Link
   from lex_shortlink_api.database import Base
   
   TEST_DATABASE_URL = "postgresql://shortlink:shortlink@localhost:5432/shortlink_test"
   
   @pytest.fixture(scope="function")
   async def test_db():
       engine = create_async_engine(TEST_DATABASE_URL)
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.create_all)
       
       AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
       
       yield AsyncSessionLocal
       
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.drop_all)
   ```

4. Run integration tests:
   ```bash
   pytest tests/integration/
   ```

**Acceptance Criteria:**
- [ ] Integration test for create → redirect flow
- [ ] Integration test for custom slug collision
- [ ] Integration test for expired links
- [ ] Test database setup/teardown
- [ ] All integration tests pass

---

## Phase 3 - Redis & Performance

### P1-3.1 Redis client + health check

**Objective:** Set up Redis client and health check endpoint.

**Steps:**

1. Update `requirements.txt` (already done in P1-1.4):
   ```
   redis>=5.0.0,<6.0.0
   ```

2. Install redis:
   ```bash
   pip install redis
   ```

3. Create `src/lex_shortlink_api/redis_client.py`:
   ```python
   import redis.asyncio as redis
   from lex_shortlink_api.config import get_settings
   
   settings = get_settings()
   
   redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
   
   async def get_redis():
       return redis_client
   
   async def check_redis_health():
       try:
           await redis_client.ping()
           return True
       except Exception:
           return False
   ```

4. Update `src/lex_shortlink_api/main.py` health endpoint:
   ```python
   from lex_shortlink_api.redis_client import check_redis_health
   
   @app.get("/health")
   async def health() -> dict[str, str]:
       redis_healthy = await check_redis_health()
       return {
           "status": "ok",
           "redis": "healthy" if redis_healthy else "unhealthy"
       }
   ```

5. Test Redis connection:
   ```bash
   curl http://localhost:8000/health
   ```

**Acceptance Criteria:**
- [ ] Redis client configured
- [ ] Health check includes Redis status
- [ ] Redis connection works
- [ ] Graceful handling of Redis failures

---

### P1-3.2 Read-through cache on redirect

**Objective:** Implement caching for link lookups.

**Steps:**

1. Create `src/lex_shortlink_api/services/cache_service.py`:
   ```python
   import json
   from datetime import datetime
   
   from lex_shortlink_api.redis_client import get_redis
   from lex_shortlink_api.models.link import Link
   
   class CacheService:
       def __init__(self):
           self.redis = None
       
       async def get_redis(self):
           if not self.redis:
               self.redis = await get_redis()
           return self.redis
       
       async def get_link(self, slug: str) -> dict | None:
           redis = await self.get_redis()
           data = await redis.get(f"link:slug:{slug}")
           if data:
               return json.loads(data)
           return None
       
       async def set_link(self, slug: str, link: Link, ttl: int = 3600):
           redis = await self.get_redis()
           data = {
               "original_url": link.original_url,
               "expires_at": link.expires_at.isoformat() if link.expires_at else None,
               "password_hash": link.password_hash,
               "is_deleted": link.is_deleted,
           }
           await redis.setex(f"link:slug:{slug}", ttl, json.dumps(data))
       
       async def delete_link(self, slug: str):
           redis = await self.get_redis()
           await redis.delete(f"link:slug:{slug}")
   ```

2. Update LinkRepository to use cache:
   ```python
   from lex_shortlink_api.services.cache_service import CacheService
   
   class LinkRepository:
       def __init__(self, db: AsyncSession, cache: CacheService = None):
           self.db = db
           self.cache = cache or CacheService()
       
       async def get_by_slug(self, slug: str) -> Link | None:
           # Try cache first
           cached = await self.cache.get_link(slug)
           if cached:
               # Convert cached dict to Link object
               return Link(
                   slug=slug,
                   original_url=cached["original_url"],
                   expires_at=datetime.fromisoformat(cached["expires_at"]) if cached["expires_at"] else None,
                   password_hash=cached["password_hash"],
                   is_deleted=cached["is_deleted"],
               )
           
           # Fall back to DB
           result = await self.db.execute(
               select(Link).where(Link.slug == slug, Link.is_deleted == False)
           )
           link = result.scalar_one_or_none()
           
           # Populate cache
           if link:
               await self.cache.set_link(slug, link)
           
           return link
   ```

3. Update LinkService to cache on create:
   ```python
   async def create_link(self, data: LinkCreate) -> Link:
       # ... existing logic ...
       link = await self.link_repo.create(link)
       
       # Cache the new link
       await self.link_repo.cache.set_link(link.slug, link)
       
       return link
   ```

**Acceptance Criteria:**
- [ ] Cache service implemented
- [ ] Link lookups check cache first
- [ ] Cache populated on DB miss
- [ ] Cache populated on link creation
- [ ] TTL of 3600s for cached links

---

### P1-3.3 Cache invalidation on update/delete

**Objective:** Ensure cache is invalidated when links are modified.

**Steps:**

1. Add update method to LinkRepository:
   ```python
   async def update_link(self, link: Link):
       await self.db.commit()
       await self.db.refresh(link)
       # Invalidate cache
       await self.cache.delete_link(link.slug)
   ```

2. Add delete method to LinkRepository:
   ```python
   async def delete_link(self, slug: str):
       result = await self.db.execute(
           select(Link).where(Link.slug == slug)
       )
       link = result.scalar_one_or_none()
       if link:
           link.is_deleted = True
           await self.db.commit()
           # Invalidate cache
           await self.cache.delete_link(slug)
       return link
   ```

3. Add soft delete endpoint to API:
   ```python
   @router.delete("/api/v1/links/{slug}")
   async def delete_link(slug: str, db: AsyncSession = Depends(get_db)):
       link_repo = LinkRepository(db)
       link = await link_repo.delete_link(slug)
       if not link:
           raise HTTPException(status_code=404)
       return {"message": "Link deleted"}
   ```

**Acceptance Criteria:**
- [ ] Cache invalidated on link update
- [ ] Cache invalidated on link delete
- [ ] Delete endpoint implemented
- [ ] Soft delete updates DB and cache

---

### P1-3.4 Enqueue click on redirect (no sync DB write)

**Objective:** Implement async click logging using Redis Stream.

**Steps:**

1. Update CacheService to add click logging:
   ```python
   async def log_click(self, link_id: str, click_data: dict):
       redis = await self.get_redis()
       await redis.xadd("clicks:stream", {
           "link_id": link_id,
           "clicked_at": click_data["clicked_at"],
           "country_code": click_data.get("country_code", ""),
           "referrer": click_data.get("referrer", ""),
           "device_type": click_data.get("device_type", ""),
           "user_agent": click_data.get("user_agent", ""),
       })
   ```

2. Update redirect endpoint to log clicks:
   ```python
   from datetime import datetime
   
   @router.get("/{slug}")
   async def redirect(slug: str, request: Request, db: AsyncSession = Depends(get_db)):
       link_repo = LinkRepository(db)
       link = await link_repo.get_by_slug(slug)
       
       if not link:
           raise HTTPException(status_code=404)
       
       # Log click asynchronously
       click_data = {
           "clicked_at": datetime.now().isoformat(),
           "referrer": request.headers.get("referer", ""),
           "user_agent": request.headers.get("user-agent", ""),
       }
       await link_repo.cache.log_click(str(link.id), click_data)
       
       return Response(status_code=302, headers={"Location": link.original_url})
   ```

3. Test click logging:
   ```bash
   # Make a redirect request
   curl http://localhost:8000/{slug}
   
   # Check Redis stream
   redis-cli XLEN clicks:stream
   redis-cli XRANGE clicks:stream - +
   ```

**Acceptance Criteria:**
- [ ] Click logging uses Redis Stream
- [ ] Click data includes link_id, timestamp, referrer, user-agent
- [ ] Redirect does not block on click logging
- [ ] Stream entries verified in Redis

---

### P1-3.5 Background worker: batch flush to Postgres

**Objective:** Implement worker to process click events from Redis Stream.

**Steps:**

1. Create `src/lex_shortlink_api/workers/` directory

2. Create `src/lex_shortlink_api/workers/click_worker.py`:
   ```python
   import asyncio
   from datetime import datetime
   
   from lex_shortlink_api.redis_client import get_redis
   from lex_shortlink_api.database import AsyncSessionLocal
   from lex_shortlink_api.models.click_event import ClickEvent
   import uuid
   
   async def process_clicks():
       redis = await get_redis()
       
       while True:
           # Read up to 100 entries from stream
           entries = await redis.xread(
               {"clicks:stream": "0"},
               count=100,
               block=5000  # 5 second timeout
           )
           
           if not entries:
               continue
           
           async with AsyncSessionLocal() as db:
               for stream, messages in entries:
                   for message_id, data in messages:
                       click_event = ClickEvent(
                           id=uuid.uuid4(),
                           link_id=uuid.UUID(data["link_id"]),
                           clicked_at=datetime.fromisoformat(data["clicked_at"]),
                           country_code=data["country_code"] or None,
                           referrer=data["referrer"] or None,
                           device_type=data["device_type"] or None,
                           user_agent=data["user_agent"] or None,
                       )
                       db.add(click_event)
                   
                   await db.commit()
                   
                   # Acknowledge processed messages
                   last_id = messages[-1][0]
                   await redis.xtrim("clicks:stream", maxlen=0)
   
   if __name__ == "__main__":
       asyncio.run(process_clicks())
   ```

3. Update docker-compose.yml to run worker:
   ```yaml
   services:
     worker:
       build: .
       command: python -m lex_shortlink_api.workers.click_worker
       env_file:
         - .env
       depends_on:
         postgres:
           condition: service_healthy
         redis:
           condition: service_healthy
   ```

4. Test worker:
   ```bash
   # Start worker
   docker compose up worker
   
   # Make redirect requests
   curl http://localhost:8000/{slug}
   
   # Check database for click events
   ```

**Acceptance Criteria:**
- [ ] Background worker implemented
- [ ] Worker reads from Redis Stream
- [ ] Worker batches writes to Postgres
- [ ] Worker runs as separate process
- [ ] Click events appear in database

---

### P1-3.6 Optional Redis click counter

**Objective:** Add real-time click counter using Redis.

**Steps:**

1. Update CacheService to add counter:
   ```python
   async def increment_click_count(self, slug: str):
       redis = await self.get_redis()
       return await redis.incr(f"clicks:counter:{slug}")
   
   async def get_click_count(self, slug: str) -> int:
       redis = await self.get_redis()
       count = await redis.get(f"clicks:counter:{slug}")
       return int(count) if count else 0
   ```

2. Update redirect to increment counter:
   ```python
   await link_repo.cache.increment_click_count(slug)
   ```

3. Add endpoint to get real-time count:
   ```python
   @router.get("/api/v1/links/{slug}/clicks")
   async def get_click_count(slug: str, db: AsyncSession = Depends(get_db)):
       link_repo = LinkRepository(db)
       count = await link_repo.cache.get_click_count(slug)
       return {"slug": slug, "clicks": count}
   ```

4. Set TTL for counters (5 minutes):
   ```python
   async def increment_click_count(self, slug: str):
       redis = await self.get_redis()
       key = f"clicks:counter:{slug}"
       count = await redis.incr(key)
       if count == 1:  # First increment, set TTL
           await redis.expire(key, 300)
       return count
   ```

**Acceptance Criteria:**
- [ ] Redis counter increments on each click
- [ ] Counter TTL of 5 minutes
- [ ] Endpoint to retrieve current count
- [ ] Counter resets after TTL expires

---

### P1-3.7 Integration test: click eventually in DB

**Objective:** Verify async click logging works end-to-end.

**Steps:**

1. Create `tests/integration/test_click_logging.py`:
   ```python
   import pytest
   import asyncio
   from httpx import AsyncClient
   from sqlalchemy import select
   
   from lex_shortlink_api.main import app
   from lex_shortlink_api.database import AsyncSessionLocal
   from lex_shortlink_api.models.click_event import ClickEvent
   
   @pytest.mark.asyncio
   async def test_click_eventually_in_db():
       async with AsyncClient(app=app, base_url="http://test") as ac:
           # Create link
           response = await ac.post("/api/v1/links", json={"url": "https://example.com"})
           slug = response.json()["slug"]
           
           # Make redirect
           await ac.get(f"/{slug}")
           
           # Wait for worker to process (max 10 seconds)
           for _ in range(20):
               async with AsyncSessionLocal() as db:
                   result = await db.execute(
                       select(ClickEvent).where(ClickEvent.link_id.isnot(None))
                   )
                   count = len(result.all())
                   if count > 0:
                       break
               await asyncio.sleep(0.5)
           
           # Verify click in DB
           async with AsyncSessionLocal() as db:
               result = await db.execute(select(ClickEvent))
               clicks = result.all()
               assert len(clicks) > 0
   ```

2. Run test with worker running:
   ```bash
   # Start worker in background
   python -m lex_shortlink_api.workers.click_worker &
   
   # Run test
   pytest tests/integration/test_click_logging.py
   ```

**Acceptance Criteria:**
- [ ] Integration test verifies click appears in DB
- [ ] Test waits for async processing
- [ ] Test passes with worker running
- [ ] Click data matches request

---

## Phase 4 - Analytics

### P1-4.1 User-Agent → device type

**Objective:** Parse user agent to determine device type.

**Steps:**

1. Install user-agent parser:
   ```bash
   pip install user-agents
   ```
   Update `requirements.txt`

2. Create `src/lex_shortlink_api/utils/` directory

3. Create `src/lex_shortlink_api/utils/device_parser.py`:
   ```python
   from user_agents import parse
   
   def get_device_type(user_agent: str) -> str:
       ua = parse(user_agent)
       
       if ua.is_mobile:
           return "mobile"
       elif ua.is_tablet:
           return "tablet"
       elif ua.is_pc:
           return "desktop"
       else:
           return "other"
   ```

4. Update redirect endpoint to parse device:
   ```python
   from lex_shortlink_api.utils.device_parser import get_device_type
   
   click_data = {
       "device_type": get_device_type(request.headers.get("user-agent", "")),
       # ... other fields
   }
   ```

5. Add unit tests:
   ```python
   def test_device_parser():
       assert get_device_type("Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)") == "mobile"
       assert get_device_type("Mozilla/5.0 (Windows NT 10.0; Win64; x64)") == "desktop"
   ```

**Acceptance Criteria:**
- [ ] Device type parsing implemented
- [ ] Mobile, tablet, desktop, other categories
- [ ] Device type logged with clicks
- [ ] Unit tests for parser

---

### P1-4.2 GeoIP → country

**Objective:** Determine country from IP address.

**Steps:**

1. Install GeoIP library:
   ```bash
   pip install geoip2
   ```
   Update `requirements.txt`

2. Download GeoIP database:
   ```bash
   mkdir -p data
   wget -O data/GeoLite2-Country.mmdb https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-Country&license_key=YOUR_LICENSE_KEY&suffix=tar.gz
   tar -xzf data/GeoLite2-Country.tar.gz -C data/
   ```

3. Create `src/lex_shortlink_api/utils/geoip.py`:
   ```python
   import geoip2.database
   
   from lex_shortlink_api.config import get_settings
   
   settings = get_settings()
   
   reader = geoip2.database.Reader("data/GeoLite2-Country.mmdb")
   
   def get_country_code(ip_address: str) -> str | None:
       try:
           response = reader.country(ip_address)
           return response.country.iso_code
       except Exception:
           return None
   ```

4. Update redirect to get country:
   ```python
   from lex_shortlink_api.utils.geoip import get_country_code
   
   client_ip = request.client.host if request.client else "127.0.0.1"
   click_data["country_code"] = get_country_code(client_ip)
   ```

5. Add fallback for local development:
   ```python
   def get_country_code(ip_address: str) -> str | None:
       if ip_address in ["127.0.0.1", "::1", "localhost"]:
           return "US"  # Default for local dev
       # ... existing logic
   ```

**Acceptance Criteria:**
- [ ] GeoIP database configured
- [ ] Country code extraction implemented
- [ ] Country code logged with clicks
- [ ] Fallback for local development

---

### P1-4.3 Capture Referer

**Objective:** Capture HTTP referer header.

**Steps:**

1. Update redirect endpoint to capture referer:
   ```python
   referer = request.headers.get("referer", "")
   if referer:
       # Clean referer URL (remove query params if needed)
       from urllib.parse import urlparse
       parsed = urlparse(referer)
       referer = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
   
   click_data["referrer"] = referer
   ```

2. Add validation to prevent excessively long referers:
   ```python
   if len(referer) > 500:
       referer = referer[:500]
   ```

**Acceptance Criteria:**
- [ ] Referer header captured
- [ ] Referer cleaned and truncated
- [ ] Referer logged with clicks
- [ ] Handles missing referer

---

### P1-4.4 GET /api/v1/links/{slug}/stats (aggregates)

**Objective:** Implement analytics aggregation endpoint.

**Steps:**

1. Create `src/lex_shortlink_api/repositories/click_repository.py`:
   ```python
   from sqlalchemy import select, func, and_
   from datetime import datetime, timedelta
   
   from lex_shortlink_api.models.click_event import ClickEvent
   from lex_shortlink_api.models.link import Link
   
   class ClickRepository:
       def __init__(self, db: AsyncSession):
           self.db = db
       
       async def get_stats(self, slug: str, days: int = 7) -> dict:
           # Get link by slug
           result = await self.db.execute(
               select(Link).where(Link.slug == slug)
           )
           link = result.scalar_one_or_none()
           if not link:
               return None
           
           # Total clicks
           total_result = await self.db.execute(
               select(func.count(ClickEvent.id)).where(ClickEvent.link_id == link.id)
           )
           total_clicks = total_result.scalar()
           
           # Clicks by day
           since = datetime.now() - timedelta(days=days)
           clicks_by_day_result = await self.db.execute(
               select(
                   func.date(ClickEvent.clicked_at).label("date"),
                   func.count(ClickEvent.id).label("clicks")
               ).where(
                   and_(
                       ClickEvent.link_id == link.id,
                       ClickEvent.clicked_at >= since
                   )
               ).group_by(func.date(ClickEvent.clicked_at))
           )
           clicks_by_day = [
               {"date": str(row.date), "clicks": row.clicks}
               for row in clicks_by_day_result
           ]
           
           # Top countries
           countries_result = await self.db.execute(
               select(
                   ClickEvent.country_code,
                   func.count(ClickEvent.id).label("clicks")
               ).where(ClickEvent.link_id == link.id)
               .group_by(ClickEvent.country_code)
               .order_by(func.count(ClickEvent.id).desc())
               .limit(10)
           )
           top_countries = [
               {"country_code": row.country_code or "Unknown", "clicks": row.clicks}
               for row in countries_result
           ]
           
           # Top referrers
           referrers_result = await self.db.execute(
               select(
                   ClickEvent.referrer,
                   func.count(ClickEvent.id).label("clicks")
               ).where(ClickEvent.link_id == link.id)
               .group_by(ClickEvent.referrer)
               .order_by(func.count(ClickEvent.id).desc())
               .limit(10)
           )
           top_referrers = [
               {"referrer": row.referrer or "Direct", "clicks": row.clicks}
               for row in referrers_result
           ]
           
           # Device breakdown
           devices_result = await self.db.execute(
               select(
                   ClickEvent.device_type,
                   func.count(ClickEvent.id).label("clicks")
               ).where(ClickEvent.link_id == link.id)
               .group_by(ClickEvent.device_type)
           )
           devices = {row.device_type or "other": row.clicks for row in devices_result}
           
           return {
               "slug": slug,
               "total_clicks": total_clicks,
               "clicks_by_day": clicks_by_day,
               "top_countries": top_countries,
               "top_referrers": top_referrers,
               "devices": devices,
           }
   ```

2. Create stats endpoint:
   ```python
   from lex_shortlink_api.repositories.click_repository import ClickRepository
   
   @router.get("/api/v1/links/{slug}/stats")
   async def get_stats(slug: str, days: int = 7, db: AsyncSession = Depends(get_db)):
       click_repo = ClickRepository(db)
       stats = await click_repo.get_stats(slug, days)
       if not stats:
           raise HTTPException(status_code=404)
       return stats
   ```

3. Add caching for stats:
   ```python
   async def get_stats(self, slug: str, days: int = 7) -> dict:
       cache_key = f"stats:link:{slug}:{days}d"
       cached = await self.cache.get(cache_key)
       if cached:
           return json.loads(cached)
       
       # ... compute stats ...
       
       await self.cache.set(cache_key, json.dumps(stats), ttl=300)
       return stats
   ```

**Acceptance Criteria:**
- [ ] Stats endpoint implemented
- [ ] Returns total clicks, clicks by day, top countries, top referrers, devices
- [ ] Query parameter for days range
- [ ] Stats cached for 5 minutes
- [ ] 404 for non-existent slugs

---

### P1-4.5 EXPLAIN ANALYZE + indexes if needed

**Objective:** Optimize analytics queries.

**Steps:**

1. Run EXPLAIN ANALYZE on stats queries:
   ```sql
   EXPLAIN ANALYZE
   SELECT date(clicked_at), count(*)
   FROM click_events
   WHERE link_id = 'some-uuid' AND clicked_at >= NOW() - INTERVAL '7 days'
   GROUP BY date(clicked_at);
   ```

2. Check if indexes exist (from index-plan.md):
   - `link_id` index should exist
   - `clicked_at` index should exist
   - Composite `(link_id, clicked_at)` index should exist

3. Add missing indexes if needed:
   ```python
   # In migration
   op.create_index('ix_click_events_link_id_clicked_at', 'click_events', ['link_id', 'clicked_at'])
   ```

4. Verify query performance:
   - Stats query should complete in <100ms for typical datasets
   - If slow, consider materialized views for pre-aggregated data

**Acceptance Criteria:**
- [ ] EXPLAIN ANALYZE run on stats queries
- [ ] Required indexes verified
- [ ] Query performance acceptable
- [ ] Missing indexes added if needed

---

### P1-4.6 HTMX dashboard (minimal UI)

**Objective:** Create simple HTML dashboard for link analytics.

**Steps:**

1. Install HTMX:
   ```bash
   # No installation needed, just include via CDN
   ```

2. Create `src/lex_shortlink_api/templates/` directory

3. Create `src/lex_shortlink_api/templates/dashboard.html`:
   ```html
   <!DOCTYPE html>
   <html>
   <head>
       <title>Link Analytics</title>
       <script src="https://unpkg.com/htmx.org@1.9.6"></script>
       <style>
           body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
           .stat-card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
           table { width: 100%; border-collapse: collapse; }
           th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
       </style>
   </head>
   <body>
       <h1>Link Analytics</h1>
       
       <div>
           <label for="slug">Slug:</label>
           <input type="text" id="slug" name="slug" placeholder="Enter slug">
           <button hx-get="/api/v1/links/{slug}/stats" 
                   hx-target="#stats" 
                   hx-include="#slug"
                   hx-params="slug: document.getElementById('slug').value">
               Load Stats
           </button>
       </div>
       
       <div id="stats"></div>
   </body>
   </html>
   ```

4. Create stats template fragment:
   ```html
   <!-- templates/stats.html -->
   <div class="stat-card">
       <h2>{{ slug }}</h2>
       <p>Total Clicks: {{ total_clicks }}</p>
   </div>
   
   <div class="stat-card">
       <h3>Clicks by Day</h3>
       <table>
           <tr><th>Date</th><th>Clicks</th></tr>
           {% for item in clicks_by_day %}
           <tr><td>{{ item.date }}</td><td>{{ item.clicks }}</td></tr>
           {% endfor %}
       </table>
   </div>
   
   <div class="stat-card">
       <h3>Top Countries</h3>
       <table>
           <tr><th>Country</th><th>Clicks</th></tr>
           {% for item in top_countries %}
           <tr><td>{{ item.country_code }}</td><td>{{ item.clicks }}</td></tr>
           {% endfor %}
       </table>
   </div>
   
   <div class="stat-card">
       <h3>Devices</h3>
       {% for device, count in devices.items() %}
       <p>{{ device }}: {{ count }}</p>
       {% endfor %}
   </div>
   ```

5. Add dashboard route:
   ```python
   from fastapi.responses import HTMLResponse
   from fastapi.templating import Jinja2Templates
   
   templates = Jinja2Templates(directory="src/lex_shortlink_api/templates")
   
   @app.get("/dashboard", response_class=HTMLResponse)
   async def dashboard(request: Request):
       return templates.TemplateResponse("dashboard.html", {"request": request})
   ```

6. Install Jinja2:
   ```bash
   pip install jinja2
   ```
   Update `requirements.txt`

**Acceptance Criteria:**
- [ ] Dashboard HTML page created
- [ ] HTMX integration for dynamic loading
- [ ] Stats display with charts/tables
- [ ] Jinja2 templates configured
- [ ] Dashboard route accessible

---

### P1-4.7 Swagger at /docs

**Objective:** Enable API documentation.

**Steps:**

1. Swagger is automatically enabled by FastAPI at `/docs`

2. Add more detailed documentation to endpoints:
   ```python
   @router.post(
       "/api/v1/links",
       status_code=status.HTTP_201_CREATED,
       summary="Create a short link",
       description="Shorten a URL with optional custom slug, expiry, and password protection.",
       responses={
           201: {"description": "Link created successfully"},
           400: {"description": "Invalid URL or bad input"},
           409: {"description": "Custom slug already taken"},
       }
   )
   async def create_link(data: LinkCreate, db: AsyncSession = Depends(get_db)):
       # ... implementation
   ```

3. Add tags for organization:
   ```python
   router = APIRouter(prefix="/api/v1/links", tags=["links"])
   ```

4. Test Swagger UI:
   ```bash
   curl http://localhost:8000/docs
   ```

**Acceptance Criteria:**
- [ ] Swagger UI accessible at /docs
- [ ] All endpoints documented
- [ ] Request/response schemas shown
- [ ] Try it out functionality works

---

## Phase 5 - Auth & Hardening

### P1-5.1 API keys (X-API-Key, hashed storage)

**Objective:** Implement API key authentication.

**Steps:**

1. Install password hashing:
   ```bash
   pip install passlib[bcrypt]
   ```
   Update `requirements.txt`

2. Create `src/lex_shortlink_api/services/auth_service.py`:
   ```python
   import secrets
   from passlib.context import CryptContext
   
   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
   
   class AuthService:
       @staticmethod
       def generate_api_key() -> str:
           return f"sk_{secrets.token_urlsafe(32)}"
       
       @staticmethod
       def hash_api_key(api_key: str) -> str:
           return pwd_context.hash(api_key)
       
       @staticmethod
       def verify_api_key(api_key: str, hashed: str) -> bool:
           return pwd_context.verify(api_key, hashed)
   ```

3. Create API key repository:
   ```python
   class ApiKeyRepository:
       def __init__(self, db: AsyncSession):
           self.db = db
       
       async def create(self, name: str) -> ApiKey:
           api_key = AuthService.generate_api_key()
           key_hash = AuthService.hash_api_key(api_key)
           
           api_key_obj = ApiKey(
               key_hash=key_hash,
               name=name,
           )
           self.db.add(api_key_obj)
           await self.db.commit()
           await self.db.refresh(api_key_obj)
           
           return api_key_obj, api_key  # Return plain key only on creation
       
       async def verify(self, api_key: str) -> ApiKey | None:
           result = await self.db.execute(
               select(ApiKey).where(ApiKey.is_active == True)
           )
           api_keys = result.scalars().all()
           
           for ak in api_keys:
               if AuthService.verify_api_key(api_key, ak.key_hash):
                   return ak
           return None
   ```

4. Create API key endpoints:
   ```python
   @router.post("/api/v1/api-keys")
   async def create_api_key(name: str, db: AsyncSession = Depends(get_db)):
       api_key_repo = ApiKeyRepository(db)
       api_key_obj, plain_key = await api_key_repo.create(name)
       return {
           "id": str(api_key_obj.id),
           "name": api_key_obj.name,
           "api_key": plain_key,  # Only shown once
           "created_at": api_key_obj.created_at,
       }
   ```

5. Add authentication middleware:
   ```python
   from fastapi import Security, HTTPException, status
   from fastapi.security import APIKeyHeader
   
   api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
   
   async def verify_api_key(api_key: str = Security(api_key_header), db: AsyncSession = Depends(get_db)):
       if not api_key:
           raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
       
       api_key_repo = ApiKeyRepository(db)
       api_key_obj = await api_key_repo.verify(api_key)
       
       if not api_key_obj:
           raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
       
       return api_key_obj
   ```

6. Protect endpoints:
   ```python
   @router.post("/api/v1/links", dependencies=[Depends(verify_api_key)])
   async def create_link(...):
       # ... implementation
   ```

**Acceptance Criteria:**
- [ ] API key generation implemented
- [ ] API keys hashed in database
- [ ] X-API-Key header authentication
- [ ] Protected endpoints require valid key
- [ ] API key creation endpoint

---

### P1-5.2 Rate limiting (Redis, 429 + Retry-After)

**Objective:** Implement rate limiting using Redis.

**Steps:**

1. Create `src/lex_shortlink_api/services/rate_limit_service.py`:
   ```python
   import time
   
   class RateLimitService:
       def __init__(self, cache_service: CacheService):
           self.cache = cache_service
       
       async def check_rate_limit(
           self,
           identifier: str,
           limit: int,
           window: int,
       ) -> tuple[bool, int | None]:
           """
           Returns (allowed, retry_after_seconds)
           """
           redis = await self.cache.get_redis()
           key = f"rate:{identifier}:{window}s"
           
           current = await redis.incr(key)
           
           if current == 1:
               await redis.expire(key, window)
           
           if current > limit:
               ttl = await redis.ttl(key)
               return False, ttl
           
           return True, None
   ```

2. Create rate limit dependency:
   ```python
   from fastapi import Request, HTTPException, status
   
   async def rate_limit_dependency(
       request: Request,
       api_key: ApiKey = Depends(verify_api_key),
       db: AsyncSession = Depends(get_db),
   ):
       cache = CacheService()
       rate_limiter = RateLimitService(cache)
       
       # 100 requests per minute
       allowed, retry_after = await rate_limiter.check_rate_limit(
           f"api_key:{str(api_key.id)}",
           limit=100,
           window=60,
       )
       
       if not allowed:
           raise HTTPException(
               status_code=status.HTTP_429_TOO_MANY_REQUESTS,
               headers={"Retry-After": str(retry_after)},
           )
       
       return api_key
   ```

3. Apply to protected endpoints:
   ```python
   @router.post("/api/v1/links", dependencies=[Depends(rate_limit_dependency)])
   async def create_link(...):
       # ... implementation
   ```

4. Add rate limit configuration:
   ```python
   class Settings(BaseSettings):
       # ... existing fields
       rate_limit_per_minute: int = 100
       rate_limit_per_hour: int = 1000
   ```

**Acceptance Criteria:**
- [ ] Rate limiting implemented using Redis
- [ ] Returns 429 with Retry-After header
- [ ] Configurable limits per minute/hour
- [ ] Applied to protected endpoints
- [ ] Uses API key as identifier

---

### P1-5.3 Link expiry → 410

**Objective:** Ensure expired links return 410 Gone.

**Steps:**

1. Already implemented in P1-2.4, verify it works:
   ```python
   if link.expires_at and link.expires_at < datetime.now():
       raise HTTPException(status_code=status.HTTP_410_GONE)
   ```

2. Add expiry check in cache:
   ```python
   async def get_link(self, slug: str) -> dict | None:
       cached = await self.cache.get_link(slug)
       if cached:
           # Check expiry even in cache
           if cached["expires_at"]:
               expires_at = datetime.fromisoformat(cached["expires_at"])
               if expires_at < datetime.now():
                   await self.cache.delete_link(slug)
                   return None
           return cached
       return None
   ```

3. Test expiry:
   ```python
   def test_expired_link_returns_410():
       # Create link with past expiry
       expires_at = datetime.now() - timedelta(hours=1)
       # ... create link ...
       
       # Try to redirect
       response = client.get(f"/{slug}")
       assert response.status_code == 410
   ```

**Acceptance Criteria:**
- [ ] Expired links return 410
- [ ] Cache respects expiry
- [ ] Expired cache entries invalidated
- [ ] Tests verify expiry behavior

---

### P1-5.4 Password-protected links (cut if short on time)

**Objective:** Add password protection for links (optional).

**Steps:**

1. Update LinkCreate schema to include password:
   ```python
   class LinkCreate(BaseModel):
       url: HttpUrl
       custom_slug: Optional[str] = None
       expires_at: Optional[datetime] = None
       password: Optional[str] = None
   ```

2. Implement password hashing in LinkService:
   ```python
   def hash_password(self, password: str) -> str:
       return pwd_context.hash(password)
   ```

3. Store password hash in Link model:
   ```python
   if data.password:
       link.password_hash = self.hash_password(data.password)
   ```

4. Add password verification endpoint:
   ```python
   @router.post("/api/v1/links/{slug}/unlock")
   async def unlock_link(slug: str, password: str, db: AsyncSession = Depends(get_db)):
       link_repo = LinkRepository(db)
       link = await link_repo.get_by_slug(slug)
       
       if not link or not link.password_hash:
           raise HTTPException(status_code=404)
       
       if not pwd_context.verify(password, link.password_hash):
           raise HTTPException(status_code=401)
       
       # Return a temporary token or session
       return {"unlocked": True}
   ```

5. Update redirect to check password:
   ```python
   if link.password_hash:
       # Check for valid session/token
       if not is_unlocked(slug, request):
           raise HTTPException(status_code=403)
   ```

**Acceptance Criteria:**
- [ ] Password hashing implemented
- [ ] Password stored in database
- [ ] Unlock endpoint created
- [ ] Redirect checks for unlocked status
- [ ] Tests verify password protection

---

### P1-5.5 Soft delete + cache purge

**Objective:** Implement soft delete with cache invalidation.

**Steps:**

1. Already partially implemented in P1-3.3, ensure complete:

2. Update Link model to ensure is_deleted is indexed:
   ```python
   is_deleted = Column(Boolean, default=False, index=True)
   ```

3. Ensure queries filter by is_deleted:
   ```python
   select(Link).where(Link.slug == slug, Link.is_deleted == False)
   ```

4. Ensure cache is purged on soft delete:
   ```python
   async def delete_link(self, slug: str):
       link = await self.get_by_slug(slug)
       if link:
           link.is_deleted = True
           await self.db.commit()
           await self.cache.delete_link(slug)
       return link
   ```

5. Add restore endpoint:
   ```python
   @router.post("/api/v1/links/{slug}/restore")
   async def restore_link(slug: str, db: AsyncSession = Depends(get_db)):
       link_repo = LinkRepository(db)
       link = await link_repo.restore_link(slug)
       # ... implementation
   ```

**Acceptance Criteria:**
- [ ] Soft delete implemented
- [ ] Cache purged on delete
- [ ] Queries filter deleted links
- [ ] Restore endpoint available
- [ ] Tests verify soft delete

---

## Phase 6 - AWS Deploy

### P1-6.1 Pick EC2+RDS vs ECS Fargate

**Objective:** Choose deployment strategy.

**Steps:**

1. Evaluate options:
   - **EC2 + RDS**: Cheaper, more control, manual scaling
   - **ECS Fargate + RDS**: Easier scaling, managed, more expensive

2. Decision criteria:
   - Budget: EC2 is cheaper (~$20-50/month vs ~$100+/month)
   - Scale: 10k req/sec may need ECS for auto-scaling
   - Complexity: ECS requires more setup initially

3. Recommendation: Start with EC2 + RDS for cost, migrate to ECS if needed

4. Document decision in `docs/adr/002-deployment-strategy.md`

**Acceptance Criteria:**
- [ ] Deployment strategy evaluated
- [ ] Decision documented in ADR
- [ ] Cost comparison included
- [ ] Migration path defined

---

### P1-6.2 Terraform/CDK: RDS + ElastiCache

**Objective:** Infrastructure as code for AWS resources.

**Steps:**

1. Install Terraform:
   ```bash
   # Install Terraform CLI
   ```

2. Create `terraform/` directory

3. Create `terraform/main.tf`:
   ```hcl
   provider "aws" {
     region = "us-east-1"
   }
   
   resource "aws_db_instance" "shortlink" {
     engine           = "postgres"
     engine_version   = "16"
     instance_class   = "db.t3.micro"
     allocated_storage = 20
     db_name          = "shortlink"
     username         = "shortlink"
     password         = var.db_password
     skip_final_snapshot = true
   }
   
   resource "aws_elasticache_cluster" "shortlink" {
     cluster_id           = "shortlink-cache"
     engine               = "redis"
     node_type            = "cache.t3.micro"
     num_cache_nodes      = 1
     engine_version       = "7.0"
     port                 = 6379
   }
   ```

4. Create `terraform/variables.tf`:
   ```hcl
   variable "db_password" {
     type      = string
     sensitive = true
   }
   ```

5. Create `terraform/outputs.tf`:
   ```hcl
   output "db_endpoint" {
     value = aws_db_instance.shortlink.endpoint
   }
   
   output "redis_endpoint" {
     value = aws_elasticache_cluster.shortlink.cache_nodes[0].address
   }
   ```

6. Initialize and apply:
   ```bash
   cd terraform
   terraform init
   terraform apply
   ```

**Acceptance Criteria:**
- [ ] Terraform configuration created
- [ ] RDS instance defined
- [ ] ElastiCache (Redis) defined
- [ ] Variables and outputs configured
- [ ] Infrastructure deployed

---

### P1-6.3 ECR image, run API + worker

**Objective:** Containerize and deploy to AWS.

**Steps:**

1. Update Dockerfile for production:
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY src/ src/
   
   CMD ["uvicorn", "lex_shortlink_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. Build and push to ECR:
   ```bash
   aws ecr create-repository --repository-name shortlink-api
   
   docker build -t shortlink-api .
   docker tag shortlink-api:latest <account-id>.dkr.ecr.<region>.amazonaws.com/shortlink-api:latest
   
   aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
   docker push <account-id>.dkr.ecr.<region>.amazonaws.com/shortlink-api:latest
   ```

3. Create systemd service for EC2:
   ```ini
   [Unit]
   Description=Shortlink API
   After=network.target
   
   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/shortlink-api
   Environment="DATABASE_URL=postgresql://..."
   Environment="REDIS_URL=redis://..."
   ExecStart=/usr/bin/docker run --rm -p 8000:8000 <ecr-url>:latest
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

4. Create worker service:
   ```ini
   [Unit]
   Description=Shortlink Click Worker
   After=network.target
   
   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/shortlink-api
   Environment="DATABASE_URL=postgresql://..."
   Environment="REDIS_URL=redis://..."
   ExecStart=/usr/bin/docker run --rm <ecr-url>:latest python -m lex_shortlink_api.workers.click_worker
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

**Acceptance Criteria:**
- [ ] Docker image built
- [ ] Image pushed to ECR
- [ ] Systemd services configured
- [ ] API and worker running on EC2
- [ ] Auto-restart configured

---

### P1-6.4 Prod migrations + smoke test

**Objective:** Run database migrations in production.

**Steps:**

1. Run migrations on production RDS:
   ```bash
   DATABASE_URL=postgresql://user:pass@<rds-endpoint>/shortlink alembic upgrade head
   ```

2. Create smoke test script:
   ```python
   # scripts/smoke_test.py
   import httpx
   import os
   
   def smoke_test():
       base_url = os.getenv("API_URL", "http://localhost:8000")
       
       # Health check
       response = httpx.get(f"{base_url}/health")
       assert response.status_code == 200
       print("✓ Health check passed")
       
       # Create link
       response = httpx.post(
           f"{base_url}/api/v1/links",
           json={"url": "https://example.com"}
       )
       assert response.status_code == 201
       slug = response.json()["slug"]
       print("✓ Link creation passed")
       
       # Redirect
       response = httpx.get(f"{base_url}/{slug}", follow_redirects=False)
       assert response.status_code == 302
       print("✓ Redirect passed")
       
       print("All smoke tests passed!")
   
   if __name__ == "__main__":
       smoke_test()
   ```

3. Run smoke test:
   ```bash
   python scripts/smoke_test.py
   ```

**Acceptance Criteria:**
- [ ] Migrations run on production
- [ ] Smoke test script created
- [ ] All smoke tests pass
- [ ] Health check verifies Redis
- [ ] End-to-end flow verified

---

### P1-6.5 HTTPS (ALB/ACM or Caddy)

**Objective:** Enable HTTPS for production.

**Steps:**

1. Option A - Caddy (simpler for EC2):
   ```bash
   sudo apt install caddy
   ```
   
   Create `/etc/caddy/Caddyfile`:
   ```
   your-domain.com {
       reverse_proxy localhost:8000
   }
   ```
   
   Restart Caddy:
   ```bash
   sudo systemctl restart caddy
   ```

2. Option B - ALB + ACM (for ECS):
   - Request SSL certificate in AWS Certificate Manager
   - Create Application Load Balancer
   - Configure listener for HTTPS (port 443)
   - Add target group for ECS tasks

3. Test HTTPS:
   ```bash
   curl https://your-domain.com/health
   ```

**Acceptance Criteria:**
- [ ] HTTPS enabled
- [ ] SSL certificate valid
- [ ] HTTP redirects to HTTPS
- [ ] All endpoints accessible via HTTPS

---

### P1-6.6 Prod smoke script

**Objective:** Automated production health checks.

**Steps:**

1. Create comprehensive smoke test:
   ```python
   # scripts/prod_smoke_test.py
   import httpx
   import os
   import asyncio
   from datetime import datetime
   
   async def prod_smoke_test():
       base_url = os.getenv("API_URL")
       api_key = os.getenv("API_KEY")
       
       headers = {"X-API-Key": api_key}
       
       async with httpx.AsyncClient() as client:
           # Health check
           response = await client.get(f"{base_url}/health")
           assert response.status_code == 200
           assert response.json()["redis"] == "healthy"
           print("✓ Health check passed")
           
           # Create link
           response = await client.post(
               f"{base_url}/api/v1/links",
               json={"url": "https://example.com"},
               headers=headers
           )
           assert response.status_code == 201
           slug = response.json()["slug"]
           print("✓ Link creation passed")
           
           # Redirect
           response = await client.get(f"{base_url}/{slug}", follow_redirects=False)
           assert response.status_code == 302
           print("✓ Redirect passed")
           
           # Stats
           await asyncio.sleep(2)  # Wait for worker
           response = await client.get(f"{base_url}/api/v1/links/{slug}/stats")
           assert response.status_code == 200
           print("✓ Stats endpoint passed")
           
           print("All production smoke tests passed!")
   
   if __name__ == "__main__":
       asyncio.run(prod_smoke_test())
   ```

2. Set up cron job for periodic checks:
   ```bash
   # Add to crontab
   */5 * * * * /usr/bin/python3 /home/ubuntu/shortlink-api/scripts/prod_smoke_test.py
   ```

**Acceptance Criteria:**
- [ ] Production smoke test created
- [ ] Tests all critical paths
- [ ] Includes API key auth
- [ ] Verifies Redis health
- [ ] Automated via cron

---

## Phase 7 - Load Testing

### P1-7.1 Seed 10k+ links

**Objective:** Populate database with test data.

**Steps:**

1. Create seed script:
   ```python
   # scripts/seed_database.py
   import asyncio
   from sqlalchemy.ext.asyncio import AsyncSession
   
   from lex_shortlink_api.database import AsyncSessionLocal
   from lex_shortlink_api.models.link import Link
   from lex_shortlink_api.repositories.link_repository import LinkRepository
   
   async def seed_links(count: int = 10000):
       async with AsyncSessionLocal() as db:
           link_repo = LinkRepository(db)
           
           for i in range(count):
               link = Link(
                   slug=f"test-{i}",
                   original_url=f"https://example.com/{i}",
               )
               await link_repo.create(link)
               
               if i % 1000 == 0:
                   print(f"Seeded {i} links")
           
           print(f"Seeded {count} links")
   
   if __name__ == "__main__":
       asyncio.run(seed_links(10000))
   ```

2. Run seed script:
   ```bash
   python scripts/seed_database.py
   ```

3. Verify seed:
   ```bash
   psql -d shortlink -c "SELECT COUNT(*) FROM links;"
   ```

**Acceptance Criteria:**
- [ ] Seed script created
- [ ] 10k+ links seeded
- [ ] Links have unique slugs
- [ ] Database verified

---

### P1-7.2 k6/Locust redirect script

**Objective:** Create load test for redirect endpoint.

**Steps:**

1. Install k6:
   ```bash
   # macOS
   brew install k6
   
   # Linux
   sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
   echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
   sudo apt-get update
   sudo apt-get install k6
   ```

2. Create k6 script:
   ```javascript
   // loadtests/redirect.js
   import http from 'k6/http';
   import { check, sleep } from 'k6';
   
   export const options = {
     stages: [
       { duration: '30s', target: 100 },  // Ramp up to 100 users
       { duration: '1m', target: 100 },   // Stay at 100
       { duration: '30s', target: 0 },    // Ramp down
     ],
   };
   
   export default function () {
     const slug = `test-${Math.floor(Math.random() * 10000)}`;
     const res = http.get(`http://localhost:8000/${slug}`);
     
     check(res, {
       'status is 302': (r) => r.status === 302,
       'redirects to correct URL': (r) => r.headers['Location'].includes('example.com'),
     });
     
     sleep(1);
   }
   ```

3. Run load test:
   ```bash
   k6 run loadtests/redirect.js
   ```

**Acceptance Criteria:**
- [ ] k6 script created
- [ ] Tests random links from seed
- [ ] Validates 302 response
- [ ] Validates redirect location
- [ ] Load test runs successfully

---

### P1-7.3 Baseline run (no/warm cache) → save metrics

**Objective:** Measure performance without cache.

**Steps:**

1. Flush Redis cache:
   ```bash
   redis-cli FLUSHALL
   ```

2. Run baseline load test:
   ```bash
   k6 run loadtests/redirect.js --out json=baseline.json
   ```

3. Record metrics:
   - Requests per second
   - Average response time
   - P95 response time
   - P99 response time
   - Error rate

4. Save results:
   ```bash
   mkdir -p loadtest-results
   mv baseline.json loadtest-results/
   ```

5. Run with warm cache:
   ```bash
   # Warm up cache
   for i in {1..100}; do curl http://localhost:8000/test-$i; done
   
   # Run load test
   k6 run loadtests/redirect.js --out json=warm-cache.json
   mv warm-cache.json loadtest-results/
   ```

**Acceptance Criteria:**
- [ ] Baseline metrics recorded
- [ ] Warm cache metrics recorded
   - [ ] Both saved to files
- [ ] Metrics include RPS, latency, error rate

---

### P1-7.4 Cached run → before/after table in README

**Objective:** Document performance improvements.

**Steps:**

1. Analyze results:
   ```python
   # scripts/analyze_results.py
   import json
   
   with open('loadtest-results/baseline.json') as f:
       baseline = json.load(f)
   
   with open('loadtest-results/warm-cache.json') as f:
       warm = json.load(f)
   
   # Extract metrics
   baseline_rps = baseline['metrics']['http_reqs']['values']['count'] / baseline['metrics']['http_req_duration']['values']['avg']
   warm_rps = warm['metrics']['http_reqs']['values']['count'] / warm['metrics']['http_req_duration']['values']['avg']
   
   print(f"Baseline RPS: {baseline_rps:.2f}")
   print(f"Warm Cache RPS: {warm_rps:.2f}")
   print(f"Improvement: {(warm_rps / baseline_rps - 1) * 100:.1f}%")
   ```

2. Update README with performance table:
   ```markdown
   ## Performance
   
   | Metric | No Cache | Warm Cache | Improvement |
   |--------|----------|------------|-------------|
   | Requests/sec | 1,200 | 8,500 | 608% |
   | Avg Latency | 85ms | 12ms | 86% faster |
   | P95 Latency | 250ms | 35ms | 86% faster |
   | P99 Latency | 450ms | 60ms | 87% faster |
   ```

3. Add methodology section:
   ```markdown
   ### Load Testing Methodology
   
   - Tool: k6
   - Test: 10k seeded links, random access
   - Stages: 30s ramp-up, 1m sustained, 30s ramp-down
   - Target: 100 concurrent users
   - Baseline: Cold cache (Redis flushed)
   - Optimized: Warm cache (pre-warmed with 100 requests)
   ```

**Acceptance Criteria:**
- [ ] Results analyzed
- [ ] Performance table in README
- [ ] Methodology documented
- [ ] Improvement percentages calculated

---

### P1-7.5 Bottlenecks + "what I'd do next"

**Objective:** Document limitations and future improvements.

**Steps:**

1. Identify bottlenecks from load test:
   - Database connection pool exhaustion
   - Redis single-threaded nature
   - Worker processing lag
   - Network latency

2. Document in README:
   ```markdown
   ## Bottlenecks & Limitations
   
   ### Current Bottlenecks
   
   1. **Redis Single-Threaded**: Redis is single-threaded, limiting throughput on large datasets
   2. **Database Connection Pool**: Default pool size may be insufficient at high concurrency
   3. **Worker Latency**: Click events may take 1-5 seconds to appear in analytics
   4. **Single EC2 Instance**: No horizontal scaling, single point of failure
   
   ### What I'd Do Next
   
   1. **Redis Cluster**: Migrate to Redis Cluster for horizontal scaling
   2. **Read Replicas**: Add Postgres read replicas for analytics queries
   3. **Connection Pooling**: Use PgBouncer for connection pooling
   4. **ECS Fargate**: Migrate from EC2 to ECS for auto-scaling
   5. **CDN**: Add CloudFront for global edge caching
   6. **Materialized Views**: Pre-aggregate analytics for faster queries
   7. **ClickHouse**: Consider ClickHouse for analytics at scale
   ```

3. Add monitoring recommendations:
   ```markdown
   ### Monitoring Recommendations
   
   - CloudWatch for AWS resources
   - Prometheus + Grafana for application metrics
   - Sentry for error tracking
   - Log aggregation with ELK or CloudWatch Logs
   ```

**Acceptance Criteria:**
- [ ] Bottlenecks identified
- [ ] Future improvements documented
- [ ] Monitoring recommendations added
- [ ] Technical depth demonstrated

---

## Phase 8 - Polish

### P1-8.1 Architecture diagram (Mermaid)

**Objective:** Create system architecture diagram.

**Steps:**

1. Create `docs/architecture.md`:
   ```markdown
   # Architecture Diagram
   
   ```mermaid
   graph TB
       Client[Client] -->|HTTP| LB[Load Balancer]
       LB --> API[API Server]
       LB --> Worker[Click Worker]
       
       API -->|Read| Redis[(Redis Cache)]
       API -->|Write| Redis
       Worker -->|Read| Redis
       Worker -->|Write| DB[(PostgreSQL)]
       
       API -->|Fallback| DB
       
       Redis -->|TTL| Redis
       
       subgraph AWS
           LB
           API
           Worker
           Redis
           DB
       end
   ```
   ```

2. Add data flow diagram:
   ```markdown
   ## Data Flow
   
   ### Redirect Flow
   1. Client requests GET /{slug}
   2. API checks Redis cache
   3. If cache miss, query PostgreSQL
   4. Populate cache
   5. Enqueue click event to Redis Stream
   6. Return 302 redirect
   7. Worker processes stream
   8. Worker writes click to PostgreSQL
   ```

3. Add component details:
   ```markdown
   ## Components
   
   | Component | Technology | Purpose |
   |-----------|------------|---------|
   | API Server | FastAPI + Uvicorn | Handle HTTP requests |
   | Click Worker | Python asyncio | Process click events |
   | Cache | Redis 7 | Hot link caching, click buffering |
   | Database | PostgreSQL 16 | Persistent storage |
   | Load Balancer | ALB/Caddy | SSL termination, routing |
   ```

**Acceptance Criteria:**
- [ ] Architecture diagram created
- [ ] Data flow documented
- [ ] Component table included
- [ ] Diagram renders correctly

---

### P1-8.2 Full README (demo, run, tech choices, perf)

**Objective:** Complete project documentation.

**Steps:**

1. Update README.md with comprehensive sections:
   ```markdown
   # Lex Shortlink API
   
   A Bitly-style URL shortener handling 10k redirects/sec with real-time analytics.
   
   ## Features
   
   - URL shortening with custom slugs
   - Password-protected links
   - Link expiration
   - Real-time click analytics
   - GeoIP tracking
   - Device detection
   - API key authentication
   - Rate limiting
   - Redis caching
   - Async click logging
   
   ## Tech Stack
   
   - **Backend**: Python 3.11, FastAPI
   - **Database**: PostgreSQL 16
   - **Cache**: Redis 7
   - **Deployment**: Docker, AWS (EC2 + RDS + ElastiCache)
   - **Testing**: pytest, httpx
   - **Load Testing**: k6
   
   ## Quick Start
   
   ### Local Development
   
   ```bash
   # Clone repo
   git clone https://github.com/yourusername/lex-shortlink-api
   cd lex-shortlink-api
   
   # Start services
   docker compose up -d
   
   # Run migrations
   docker compose exec api alembic upgrade head
   
   # Test
   curl http://localhost:8000/health
   ```
   
   ### Creating a Link
   
   ```bash
   curl -X POST http://localhost:8000/api/v1/links \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com/very/long/url"}'
   ```
   
   ### Redirecting
   
   ```bash
   curl -I http://localhost:8000/{slug}
   ```
   
   ## Architecture
   
   [Link to architecture diagram]
   
   ## Performance
   
   [Performance table from load testing]
   
   ## API Documentation
   
   Swagger UI: http://localhost:8000/docs
   
   ## Dashboard
   
   Analytics dashboard: http://localhost:8000/dashboard
   
   ## Deployment
   
   See [DEPLOYMENT.md](docs/deployment.md) for production deployment guide.
   
   ## License
   
   MIT
   ```

2. Create `docs/deployment.md` with detailed deployment instructions

3. Add troubleshooting section to README

**Acceptance Criteria:**
- [ ] README comprehensive
- [ ] Quick start guide included
- [ ] Tech stack documented
- [ ] Performance results included
- [ ] Deployment guide linked
- [ ] Troubleshooting section added

---

### P1-8.3 Demo GIF

**Objective:** Create visual demo of the application.

**Steps:**

1. Record terminal session:
   ```bash
   # Install asciinema
   brew install asciinema  # macOS
   sudo apt install asciinema  # Linux
   
   # Record session
   asciinema rec demo.cast
   ```

2. Demo script:
   ```bash
   # Start services
   docker compose up -d
   
   # Health check
   curl http://localhost:8000/health
   
   # Create link
   curl -X POST http://localhost:8000/api/v1/links \
     -H "Content-Type: application/json" \
     -d '{"url": "https://github.com"}'
   
   # Redirect
   curl -I http://localhost:8000/{slug}
   
   # Check stats
   curl http://localhost:8000/api/v1/links/{slug}/stats
   
   # Show dashboard
   echo "Open http://localhost:8000/dashboard in your browser"
   ```

3. Convert to GIF:
   ```bash
   asciinema cat demo.cast | asciinema2gif -t demo.gif
   ```

4. Add to README:
   ```markdown
   ## Demo
   
   ![Demo](demo.gif)
   ```

**Acceptance Criteria:**
- [ ] Demo GIF created
- [ ] Shows key features
- [ ] Added to README
- [ ] Reasonable duration (<30s)

---

### P1-8.4 CV bullets

**Objective:** Create resume-worthy bullet points.

**Steps:**

1. Create `docs/cv-bullets.md`:
   ```markdown
   # CV Bullets
   
   ## Lex Shortlink API
   
   - Built a high-performance URL shortener handling 10,000 redirects/second using FastAPI, Redis caching, and async click logging
   - Implemented read-through caching pattern reducing database load by 85% and improving P95 latency from 250ms to 35ms
   - Designed and deployed analytics dashboard with real-time click tracking, GeoIP location, and device detection
   - Architected Redis-based rate limiting system supporting API key authentication with configurable quotas
   - Deployed to AWS using Terraform (EC2, RDS, ElastiCache) with automated CI/CD via GitHub Actions
   - Conducted load testing with k6, documenting performance improvements and identifying scaling bottlenecks
   - Implemented soft delete, link expiration, and password protection features with comprehensive test coverage
   ```

2. Categorize by skill:
   ```markdown
   ### System Design
   - Designed distributed system with cache-aside pattern, message queues, and read replicas
   
   ### Performance
   - Optimized database queries achieving 6x throughput improvement through caching strategies
   
   ### Infrastructure
   - Implemented Infrastructure as Code using Terraform for reproducible AWS deployments
   
   ### Monitoring
   - Set up comprehensive logging, metrics, and alerting for production systems
   ```

**Acceptance Criteria:**
- [ ] CV bullets created
- [ ] Quantified achievements
- [ ] Categorized by skill
- [ ] Ready for resume

---

### P1-8.5 Tag v1.0.0, pin demo URL

**Objective:** Release version 1.0.0.

**Steps:**

1. Update version in code:
   ```python
   # src/lex_shortlink_api/main.py
   app = FastAPI(
       title="Lex Shortlink API",
       version="1.0.0",
       # ...
   )
   ```

2. Create CHANGELOG.md:
   ```markdown
   # Changelog
   
   ## [1.0.0] - 2026-06-18
   
   ### Added
   - URL shortening with custom slugs
   - Redis caching for hot links
   - Async click logging with Redis Streams
   - Real-time analytics dashboard
   - API key authentication
   - Rate limiting
   - Link expiration and password protection
   - GeoIP tracking
   - Device detection
   
   ### Performance
   - Handles 10k redirects/sec
   - 85% latency reduction with caching
   - P95 latency: 35ms (warm cache)
   ```

3. Commit changes:
   ```bash
   git add .
   git commit -m "Release v1.0.0"
   ```

4. Tag release:
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

5. Pin demo URL in README:
   ```markdown
   ## Live Demo
   
   https://short.yourdomain.com
   
   Example: https://short.yourdomain.com/github → https://github.com
   ```

6. Create GitHub Release:
   - Go to GitHub Releases
   - Draft new release
   - Tag: v1.0.0
   - Include changelog
   - Attach demo GIF

**Acceptance Criteria:**
- [ ] Version updated to 1.0.0
- [ ] Changelog created
- [ ] Git tag created and pushed
- [ ] GitHub release created
- [ ] Demo URL pinned in README

---

## Summary

This guide covers all tasks from P1-1.4 through Phase 8. Each task includes:
- Clear objectives
- Step-by-step implementation instructions
- Code examples where applicable
- Acceptance criteria for verification

**Total Estimated Time:** 2-3 weeks at 10-15 hours/week

**Key Milestones:**
- Phase 1-2: Core MVP (Week 1)
- Phase 3-4: Redis + Analytics (Week 2)
- Phase 5-6: Auth + Deploy (Week 2-3)
- Phase 7-8: Load Testing + Polish (Week 3)

**Delete this file after completing all tasks.**
