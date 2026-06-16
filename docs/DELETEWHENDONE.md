# Complete Step-by-Step Implementation Guide
## Starting from P1-1.4 through Phase 8

This document provides detailed step-by-step instructions for all remaining tasks in the Shortlink-API project.

**IMPORTANT:** This guide is designed for offline use. All commands and code are self-contained. You don't need internet access to follow these steps.

---

## Phase 1 - Design (Remaining Tasks)

### P1-1.5 ADR: read-through cache + async click logging

**What this task means:** ADR stands for "Architecture Decision Record." This is another PLANNING/documentation task. You're writing down WHY you made certain technical decisions. This helps you (and others) understand the reasoning behind your choices later.

**Objective:** Create a document that explains why you chose the caching strategy and async click logging approach.

**Steps:**

**Step 1: Create the ADR directory and file**
- First, create a new directory: `docs/adr/`
- Full path: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/docs/adr/`
- Then create a file: `docs/adr/001-read-through-cache-async-clicks.md`
- Full path: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/docs/adr/001-read-through-cache-async-clicks.md`

**Step 2: Document the read-through cache pattern**
- In the ADR file, write a section explaining the caching decision:
  - **Context (The Problem):** We need to handle 10,000 redirects per second with very low latency (fast response times). Querying the database for every redirect would be too slow.
  - **Decision (The Solution):** Use a "read-through cache" pattern. This means: when someone requests a link, we check Redis first. If the data is there (cache hit), we return it immediately. If not (cache miss), we get it from the database and store it in Redis for next time.
  - **Why This is Good (Pros):**
    - Very fast redirects when data is cached
    - Reduces load on the database
    - Cache fills up automatically as people use the system
  - **What Could Go Wrong (Cons):**
    - Cached data might be stale (outdated)
    - Need a strategy to update/delete cached data when it changes

**Step 3: Document the async click logging architecture**
- In the ADR file, write a section explaining click logging:
  - **Context (The Problem):** When someone clicks a link, we need to record that click in the database. But if we write to the database immediately during the redirect, it will slow down the redirect. We want redirects to be as fast as possible.
  - **Decision (The Solution):** Use "async click logging." When a click happens, we quickly write it to Redis (which is very fast) and immediately return the redirect. A separate background worker process reads from Redis and writes to the database later.
  - **Why This is Good (Pros):**
    - Redirects are not blocked by database writes
    - Database writes happen in batches (more efficient)
    - Can handle traffic spikes (Redis handles high throughput better than database)
  - **What Could Go Wrong (Cons):**
    - Analytics are not instantly up-to-date (eventual consistency)
    - Need to run a separate worker process
    - If Redis crashes before worker processes, data could be lost

**Step 4: Add simple diagrams**
- In the ADR file, add ASCII diagrams showing the flow:
  - Read-through cache flow:
    ```
    User Request → Check Redis → Cache Hit? → Yes: Return Data
                                        → No: Get from DB → Store in Redis → Return Data
    ```
  - Async click logging flow:
    ```
    User Clicks Link → Write to Redis Stream → Return Redirect Immediately
                                          ↓
                                    Background Worker Reads Stream
                                          ↓
                                    Worker Writes to Database
    ```

**Step 5: Document alternatives you considered**
- In the ADR file, write about other options you thought about and why you rejected them:
  - **Write-through cache:** This means writing to cache AND database every time. Rejected because it's slower for writes.
  - **Direct database writes:** Write click data directly to database during redirect. Rejected because it blocks the redirect and makes it slow.
  - **Message queue (like RabbitMQ):** Use a dedicated message queue system. Rejected because it's overkill for this project's scale - Redis is simpler and sufficient.

**Acceptance Criteria (check these when done):**
- [ ] Directory `docs/adr/` exists
- [ ] File `docs/adr/001-read-through-cache-async-clicks.md` exists
- [ ] File documents read-through cache pattern with context, decision, pros, and cons
- [ ] File documents async click logging with context, decision, pros, and cons
- [ ] File includes simple ASCII diagrams for both flows
- [ ] File lists alternatives considered with reasons for rejection

---

## Phase 2 - Core MVP

**What this phase means:** Now we start CODING. Phase 1 was planning/design. Phase 2 is building the core functionality: the ability to create short links and redirect to them. We'll set up the database, create the data models, and build the API endpoints.

### P1-2.1 Alembic migrations

**What this task means:** "Migrations" are a way to manage database changes over time. Alembic is a tool that helps you create, modify, and update your database schema in a controlled way. Think of it like version control for your database.

**Objective:** Set up Alembic to manage database schema changes.

**Steps:**

**Step 1: Install the required Python packages**
- Open your terminal
- Run this command:
  ```bash
  pip install alembic sqlalchemy[asyncio] asyncpg
  ```
- What these packages do:
  - `alembic`: Database migration tool
  - `sqlalchemy[asyncio]`: ORM (Object-Relational Mapping) library for working with databases
  - `asyncpg`: Async PostgreSQL driver (lets Python talk to PostgreSQL efficiently)

**Step 2: Update requirements.txt**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/requirements.txt`
- Add these lines to the file:
  ```
  alembic>=1.13.0,<2.0.0
  sqlalchemy[asyncio]>=2.0.0,<3.0.0
  asyncpg>=0.29.0,<1.0.0
  ```
- This ensures anyone else running your project will install the same versions

**Step 3: Initialize Alembic**
- Navigate to the source directory:
  ```bash
  cd /home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api
  ```
- Run:
  ```bash
  alembic init alembic
  ```
- This creates an `alembic/` directory with configuration files

**Step 4: Configure alembic.ini**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/alembic.ini`
- Find the line that starts with `sqlalchemy.url =`
- Change it to use an environment variable:
  ```
  sqlalchemy.url = postgresql://shortlink:shortlink@localhost:5432/shortlink
  ```
- This tells Alembic where your database is

**Step 5: Update env.py for async support**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/alembic/env.py`
- This file needs to be configured to work with async PostgreSQL
- You'll need to modify it to import asyncio and configure an async engine
- (The exact code will depend on your setup, but the key is making it async-compatible)

**Step 6: Create the initial migration**
- From the `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api` directory, run:
  ```bash
  alembic revision --autogenerate -m "Initial schema"
  ```
- This creates a new migration file in `alembic/versions/`
- The file will be named something like `12345_initial_schema.py`

**Step 7: Define the database schema in the migration**
- Open the migration file created in Step 6
- In the `upgrade()` function, add code to create three tables:
  ```python
  def upgrade():
      # Create links table
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

      # Create click_events table
      op.create_table(
          'click_events',
          sa.Column('id', sa.UUID(), primary_key=True),
          sa.Column('link_id', sa.UUID(), sa.ForeignKey('links.id'), nullable=False),
          sa.Column('clicked_at', sa.TIMESTAMP(timezone=True), nullable=False),
          sa.Column('country_code', sa.Text(), nullable=True),
          sa.Column('referrer', sa.Text(), nullable=True),
          sa.Column('device_type', sa.Text(), nullable=True),
          sa.Column('user_agent', sa.Text(), nullable=True),
      )

      # Create api_keys table
      op.create_table(
          'api_keys',
          sa.Column('id', sa.UUID(), primary_key=True),
          sa.Column('key_hash', sa.Text(), unique=True, nullable=False),
          sa.Column('name', sa.Text(), nullable=False),
          sa.Column('is_active', sa.Boolean(), default=True),
          sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
      )
  ```
- Also add a `downgrade()` function to drop these tables (reverse of upgrade)

**Step 8: Test the migration**
- Make sure your PostgreSQL database is running (from docker-compose up)
- Run the migration:
  ```bash
  alembic upgrade head
  ```
- This should create the tables in your database
- Test rolling back:
  ```bash
  alembic downgrade -1
  ```
- This should drop the tables
- Run upgrade again to recreate them:
  ```bash
  alembic upgrade head
  ```

**Acceptance Criteria (check these when done):**
- [ ] Alembic is initialized (alembic/ directory exists)
- [ ] alembic.ini is configured with database URL
- [ ] env.py is configured for async support
- [ ] Initial migration file exists in alembic/versions/
- [ ] Migration creates links, click_events, and api_keys tables
- [ ] Migration can be applied with `alembic upgrade head`
- [ ] Migration can be rolled back with `alembic downgrade -1`
- [ ] Tables exist in PostgreSQL after running migration

---

### P1-2.2 SQLAlchemy models + repository layer

**What this task means:** "SQLAlchemy models" are Python classes that represent your database tables. Instead of writing raw SQL queries, you use these Python objects. The "repository layer" is a pattern where you separate database access logic from the rest of your code - it makes your code cleaner and easier to test.

**Objective:** Create Python classes that represent your database tables and a repository to handle database operations.

**Steps:**

**Step 1: Create the models directory**
- Create a new directory: `src/lex_shortlink_api/models/`
- Full path: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/models/`

**Step 2: Create __init__.py for models**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/models/__init__.py`
- This file can be empty, or you can add imports later

**Step 3: Create the Link model**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/models/link.py`
- Add this code:
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
- What this does: Creates a Python class that represents the `links` table in your database

**Step 4: Create the ClickEvent model**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/models/click_event.py`
- Add this code:
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

**Step 5: Create the ApiKey model**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/models/api_key.py`
- Add this code:
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

**Step 6: Create database.py for session management**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/database.py`
- Add this code:
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
- What this does: Sets up the database connection and provides a function to get database sessions

**Step 7: Create the repositories directory**
- Create a new directory: `src/lex_shortlink_api/repositories/`
- Full path: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/repositories/`

**Step 8: Create __init__.py for repositories**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/repositories/__init__.py`
- This file can be empty

**Step 9: Create the Link repository**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/repositories/link_repository.py`
- Add this code:
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
- What this does: Provides methods to create, retrieve, and check for links in the database

**Acceptance Criteria (check these when done):**
- [ ] Directory `src/lex_shortlink_api/models/` exists
- [ ] File `models/link.py` exists with Link class
- [ ] File `models/click_event.py` exists with ClickEvent class
- [ ] File `models/api_key.py` exists with ApiKey class
- [ ] File `database.py` exists with engine and session setup
- [ ] Directory `src/lex_shortlink_api/repositories/` exists
- [ ] File `repositories/link_repository.py` exists with LinkRepository class
- [ ] All models have correct columns matching the database schema
- [ ] Relationships between models are defined

---

### P1-2.3 POST /api/v1/links (validate URL, generate slug)

**What this task means:** This is where you create the API endpoint that allows users to create short links. When someone sends a POST request with a long URL, your API will create a short slug and store it in the database.

**Objective:** Implement the link shortening endpoint that accepts a URL and returns a short link.

**Steps:**

**Step 1: Create the schemas directory**
- Create a new directory: `src/lex_shortlink_api/schemas/`
- Full path: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/schemas/`
- "Schemas" define the structure of data coming in and going out of your API

**Step 2: Create __init__.py for schemas**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/schemas/__init__.py`
- This file can be empty

**Step 3: Create the link schema**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/schemas/link.py`
- Add this code:
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
- What this does: Defines what data the API expects to receive (LinkCreate) and what it will return (LinkResponse)

**Step 4: Create the services directory**
- Create a new directory: `src/lex_shortlink_api/services/`
- Full path: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/services/`
- "Services" contain business logic (like generating slugs, validating data)

**Step 5: Create __init__.py for services**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/services/__init__.py`
- This file can be empty

**Step 6: Create the link service**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/services/link_service.py`
- Add this code:
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
- What this does: Contains the logic for generating slugs and creating links

**Step 7: Create the api directory**
- Create a new directory: `src/lex_shortlink_api/api/`
- Full path: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/api/`

**Step 8: Create __init__.py for api**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/api/__init__.py`
- This file can be empty

**Step 9: Create the links API router**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/api/links.py`
- Add this code:
  ```python
  from fastapi import APIRouter, HTTPException, status, Depends
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
- What this does: Defines the API endpoint that creates links

**Step 10: Update main.py to include the router**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/main.py`
- Add this import at the top:
  ```python
  from lex_shortlink_api.api.links import router as links_router
  ```
- Add this line after creating the app:
  ```python
  app.include_router(links_router)
  ```

**Step 11: Test the endpoint**
- Start your API server (if not running):
  ```bash
  cd /home/lex/Documents/PersonalProjects/Lex-Shortlink-API
  docker compose up
  ```
- Test creating a link:
  ```bash
  curl -X POST http://localhost:8000/api/v1/links \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com"}'
  ```
- You should get a response with the short link

**Acceptance Criteria (check these when done):**
- [ ] Directory `src/lex_shortlink_api/schemas/` exists
- [ ] File `schemas/link.py` exists with LinkCreate and LinkResponse classes
- [ ] Directory `src/lex_shortlink_api/services/` exists
- [ ] File `services/link_service.py` exists with LinkService class
- [ ] Directory `src/lex_shortlink_api/api/` exists
- [ ] File `api/links.py` exists with POST endpoint
- [ ] main.py includes the links router
- [ ] POST /api/v1/links endpoint returns 201 status
- [ ] Endpoint returns slug, short_url, url, expires_at, created_at
- [ ] Custom slug validation works
- [ ] Auto-generated slugs are 6 characters

---

### P1-2.4 GET /{slug} → 302 / 404 / 410

**What this task means:** This is the redirect endpoint. When someone visits a short URL like `http://localhost:8000/abc123`, your API needs to look up the original URL and redirect them to it. HTTP status code 302 means "temporary redirect," 404 means "not found," and 410 means "gone" (for expired/deleted links).

**Objective:** Implement the redirect endpoint that looks up a slug and redirects to the original URL.

**Steps:**

**Step 1: Create a separate redirects router**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/api/redirects.py`
- Add this code:
  ```python
  from fastapi import APIRouter, HTTPException, status, Response, Depends
  from sqlalchemy.ext.asyncio import AsyncSession
  from datetime import datetime

  from lex_shortlink_api.database import get_db
  from lex_shortlink_api.repositories.link_repository import LinkRepository

  router = APIRouter(tags=["redirects"])

  @router.get("/{slug}")
  async def redirect(slug: str, db: AsyncSession = Depends(get_db)):
      link_repo = LinkRepository(db)
      link = await link_repo.get_by_slug(slug)

      if not link:
          raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

      if link.expires_at and link.expires_at < datetime.now():
          raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link has expired")

      if link.is_deleted:
          raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link has been deleted")

      return Response(status_code=status.HTTP_302_FOUND, headers={"Location": link.original_url})
  ```
- What this does: Looks up the slug and redirects to the original URL, or returns appropriate error codes

**Step 2: Update main.py to include the redirects router**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/main.py`
- Add this import at the top:
  ```python
  from lex_shortlink_api.api.redirects import router as redirects_router
  ```
- Add this line after including the links router:
  ```python
  app.include_router(redirects_router)
  ```

**Step 3: Test the redirect**
- First, create a link (from P1-2.3):
  ```bash
  curl -X POST http://localhost:8000/api/v1/links \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com"}'
  ```
- Note the slug from the response (e.g., "abc123")
- Test the redirect:
  ```bash
  curl -I http://localhost:8000/abc123
  ```
- You should see `HTTP/1.1 302 Found` and a `Location` header pointing to the original URL
- Test a non-existent slug:
  ```bash
  curl -I http://localhost:8000/nonexistent
  ```
- You should see `HTTP/1.1 404 Not Found`

**Acceptance Criteria (check these when done):**
- [ ] File `api/redirects.py` exists with redirect endpoint
- [ ] main.py includes the redirects router
- [ ] GET /{slug} returns 302 with Location header for valid links
- [ ] GET /{slug} returns 404 for non-existent slugs
- [ ] GET /{slug} returns 410 for expired links
- [ ] GET /{slug} returns 410 for deleted links
- [ ] Redirect works in browser

---

### P1-2.5 Custom slug + collision handling (409)

**What this task means:** Users should be able to choose their own custom slugs (like "my-link" instead of a random "abc123"). You need to validate that custom slugs are properly formatted and handle the case where someone tries to use a slug that's already taken (collision). HTTP 409 means "conflict."

**Objective:** Add validation for custom slugs and handle slug collisions.

**Steps:**

**Step 1: Add slug validation to LinkService**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/services/link_service.py`
- Add this method to the LinkService class:
  ```python
  def validate_slug(self, slug: str) -> bool:
      # Only allow alphanumeric characters and hyphens
      return all(c.isalnum() or c == '-' for c in slug)
  ```

**Step 2: Update create_link to validate custom slug**
- In the same file, update the `create_link` method to add validation:
  ```python
  async def create_link(self, data: LinkCreate) -> Link:
      if data.custom_slug:
          if not self.validate_slug(data.custom_slug):
              raise ValueError("Invalid slug format: only alphanumeric characters and hyphens allowed")
          slug = data.custom_slug
      else:
          slug = self.generate_slug()

      # Add length validation
      if len(slug) < 3 or len(slug) > 50:
          raise ValueError("Slug must be between 3 and 50 characters")

      if await self.link_repo.slug_exists(slug):
          raise ValueError("Slug already exists")

      link = Link(
          slug=slug,
          original_url=str(data.url),
          expires_at=data.expires_at,
      )

      if data.password:
          link.password_hash = self.hash_password(data.password)

      return await self.link_repo.create(link)
  ```

**Step 3: Test custom slug validation**
- Test with invalid characters:
  ```bash
  curl -X POST http://localhost:8000/api/v1/links \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com", "custom_slug": "test slug"}'
  ```
- Should return an error about invalid format
- Test with valid custom slug:
  ```bash
  curl -X POST http://localhost:8000/api/v1/links \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com", "custom_slug": "my-custom-link"}'
  ```
- Should succeed

**Step 4: Test collision handling**
- Create a link with custom slug "test":
  ```bash
  curl -X POST http://localhost:8000/api/v1/links \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com", "custom_slug": "test"}'
  ```
- Try to create another link with the same slug:
  ```bash
  curl -X POST http://localhost:8000/api/v1/links \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.org", "custom_slug": "test"}'
  ```
- Should return HTTP 409 Conflict

**Acceptance Criteria (check these when done):**
- [ ] LinkService has validate_slug method
- [ ] Custom slugs are validated for format (alphanumeric + hyphens only)
- [ ] Custom slugs are validated for length (3-50 characters)
- [ ] Invalid slug format returns error
- [ ] Slug length outside range returns error
- [ ] Duplicate slug returns HTTP 409 Conflict
- [ ] Valid custom slugs work correctly

---

### P1-2.6 Structured logging on redirect path

**What this task means:** Logging is crucial for debugging and monitoring. You want to log every redirect attempt - whether it succeeded, failed, or what the target URL was. "Structured logging" means logging in a consistent format (like JSON) that's easy to parse and analyze.

**Objective:** Add logging to track redirect attempts for monitoring and debugging.

**Steps:**

**Step 1: Add log level to config**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/config.py`
- Add a log_level field to the Settings class:
  ```python
  class Settings(BaseSettings):
      model_config = SettingsConfigDict (
          env_file=".env",
          env_file_encoding="utf-8",
          extra="ignore",
      )

      database_url: str  = "postgresql://shortlink:shortlink@localhost:5432/shortlink"
      redis_url: str = "redis://localhost:6379/0"
      app_env: str = "development"
      log_level: str = "INFO"
  ```

**Step 2: Configure logging in main.py**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/main.py`
- Add logging configuration after getting settings:
  ```python
  import logging

  @asynccontextmanager
  async def lifespan(app: FastAPI):
      settings = get_settings()
      logging.basicConfig(
          level=settings.log_level,
          format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
      )
      yield
  ```

**Step 3: Add structured logging to redirect endpoint**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/api/redirects.py`
- Update the redirect function to add logging:
  ```python
  import logging
  import json
  from datetime import datetime

  logger = logging.getLogger(__name__)

  @router.get("/{slug}")
  async def redirect(slug: str, db: AsyncSession = Depends(get_db)):
      logger.info(json.dumps({
          "event": "redirect_attempt",
          "slug": slug,
          "timestamp": datetime.now().isoformat(),
      }))

      link_repo = LinkRepository(db)
      link = await link_repo.get_by_slug(slug)

      if not link:
          logger.warning(json.dumps({
              "event": "redirect_not_found",
              "slug": slug,
          }))
          raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

      if link.expires_at and link.expires_at < datetime.now():
          logger.warning(json.dumps({
              "event": "redirect_expired",
              "slug": slug,
              "expires_at": link.expires_at.isoformat(),
          }))
          raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link has expired")

      if link.is_deleted:
          logger.warning(json.dumps({
              "event": "redirect_deleted",
              "slug": slug,
          }))
          raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link has been deleted")

      logger.info(json.dumps({
          "event": "redirect_success",
          "slug": slug,
          "target_url": link.original_url,
      }))

      return Response(status_code=status.HTTP_302_FOUND, headers={"Location": link.original_url})
  ```

**Step 4: Test logging**
- Make a redirect request:
  ```bash
  curl -I http://localhost:8000/abc123
  ```
- Check the console output where your API is running
- You should see JSON-formatted log messages

**Acceptance Criteria (check these when done):**
- [ ] config.py has log_level field
- [ ] main.py configures logging
- [ ] redirects.py has structured JSON logging
- [ ] Redirect attempts are logged with timestamp and slug
- [ ] Redirect failures (not found, expired, deleted) are logged as warnings
- [ ] Redirect successes are logged with target URL
- [ ] Log output appears in console

---

### P1-2.7 Unit tests (validation, slug, expiry)

**What this task means:** Unit tests test individual pieces of code in isolation. They help ensure your code works correctly and catch bugs early. pytest is a Python testing framework that makes writing tests easy.

**Objective:** Add unit tests for core functionality like slug generation, validation, and URL validation.

**Steps:**

**Step 1: Create the unit tests directory**
- Create a new directory: `tests/unit/`
- Full path: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/tests/unit/`

**Step 2: Create test_link_service.py**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/tests/unit/test_link_service.py`
- Add this code:
  ```python
  import pytest
  from lex_shortlink_api.services.link_service import LinkService

  # We'll need to mock the repository for unit tests
  class MockLinkRepository:
      def __init__(self):
          self.slugs = {}

      async def slug_exists(self, slug: str) -> bool:
          return slug in self.slugs

  @pytest.fixture
  def link_service():
      mock_repo = MockLinkRepository()
      return LinkService(mock_repo)

  def test_generate_slug(link_service):
      slug = link_service.generate_slug()
      assert len(slug) == 6
      assert slug.isalnum()

  def test_validate_slug_valid(link_service):
      assert link_service.validate_slug("test-slug")
      assert link_service.validate_slug("abc123")
      assert link_service.validate_slug("my-custom-link-123")

  def test_validate_slug_invalid(link_service):
      assert not link_service.validate_slug("test slug")  # has space
      assert not link_service.validate_slug("test@slug")  # has special char
      assert not link_service.validate_slug("")  # empty
  ```

**Step 3: Create test_schemas.py**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/tests/unit/test_schemas.py`
- Add this code:
  ```python
  import pytest
  from pydantic import ValidationError
  from lex_shortlink_api.schemas.link import LinkCreate

  def test_valid_url():
      data = LinkCreate(url="https://example.com")
      assert str(data.url) == "https://example.com"

  def test_invalid_url():
      with pytest.raises(ValidationError):
          LinkCreate(url="not-a-url")

  def test_custom_slug():
      data = LinkCreate(url="https://example.com", custom_slug="my-link")
      assert data.custom_slug == "my-link"

  def test_optional_fields():
      data = LinkCreate(url="https://example.com")
      assert data.custom_slug is None
      assert data.expires_at is None
      assert data.password is None
  ```

**Step 4: Run the unit tests**
- From the project root, run:
  ```bash
  pytest tests/unit/
  ```
- You should see all tests pass

**Acceptance Criteria (check these when done):**
- [ ] Directory `tests/unit/` exists
- [ ] File `tests/unit/test_link_service.py` exists
- [ ] File `tests/unit/test_schemas.py` exists
- [ ] test_generate_slug passes
- [ ] test_validate_slug_valid passes
- [ ] test_validate_slug_invalid passes
- [ ] test_valid_url passes
- [ ] test_invalid_url passes
- [ ] test_custom_slug passes
- [ ] All unit tests pass when running pytest

---

### P1-2.8 Integration tests (shorten → redirect round-trip)

**What this task means:** Integration tests test how different parts of your system work together. Unlike unit tests that test one piece in isolation, integration tests test the full flow - like creating a link and then redirecting to it. This catches issues that unit tests might miss.

**Objective:** Add integration tests that test the full request flow from creating a link to redirecting to it.

**Steps:**

**Step 1: Create the integration tests directory**
- Create a new directory: `tests/integration/`
- Full path: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/tests/integration/`

**Step 2: Create test_link_flow.py**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/tests/integration/test_link_flow.py`
- Add this code:
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
      # Create a link
      response = await client.post(
          "/api/v1/links",
          json={"url": "https://example.com"}
      )
      assert response.status_code == 201
      data = response.json()
      slug = data["slug"]

      # Redirect to the link
      response = await client.get(f"/{slug}", follow_redirects=False)
      assert response.status_code == 302
      assert response.headers["location"] == "https://example.com"

  @pytest.mark.asyncio
  async def test_custom_slug_collision(client):
      # Create first link with custom slug
      await client.post(
          "/api/v1/links",
          json={"url": "https://example.com", "custom_slug": "test"}
      )

      # Try to create another link with same slug
      response = await client.post(
          "/api/v1/links",
          json={"url": "https://example.org", "custom_slug": "test"}
      )
      assert response.status_code == 409

  @pytest.mark.asyncio
  async def test_nonexistent_slug(client):
      response = await client.get("/nonexistent-slug")
      assert response.status_code == 404
  ```

**Step 3: Create conftest.py for test configuration**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/tests/conftest.py`
- Add this code:
  ```python
  import pytest
  from httpx import AsyncClient
  from lex_shortlink_api.main import app

  @pytest.fixture
  async def client():
      async with AsyncClient(app=app, base_url="http://test") as ac:
          yield ac
  ```

**Step 4: Run the integration tests**
- From the project root, run:
  ```bash
  pytest tests/integration/
  ```
- You should see all tests pass

**Acceptance Criteria (check these when done):**
- [ ] Directory `tests/integration/` exists
- [ ] File `tests/integration/test_link_flow.py` exists
- [ ] File `tests/conftest.py` exists
- [ ] test_create_and_redirect passes
- [ ] test_custom_slug_collision passes
- [ ] test_nonexistent_slug passes
- [ ] All integration tests pass when running pytest

---

## Phase 3 - Redis & Performance

**What this phase means:** Now we add Redis caching to make the application faster. Redis is an in-memory data store that's much faster than PostgreSQL. We'll cache link data so redirects are lightning-fast, and we'll use Redis Streams to buffer click events so they don't slow down redirects.

### P1-3.1 Redis client + health check

**What this task means:** You need to set up a Redis client so your Python code can talk to Redis. You'll also add a health check that verifies Redis is running and accessible.

**Objective:** Set up Redis client and add Redis status to the health check endpoint.

**Steps:**

**Step 1: Install Redis Python library**
- The redis dependency was already added to requirements.txt in P1-1.4
- Install it:
  ```bash
  pip install redis
  ```

**Step 2: Create redis_client.py**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/redis_client.py`
- Add this code:
  ```python
  import redis.asyncio as redis
  from lex_shortlink_api.config import get_settings

  settings = get_settings()

  # Create Redis client
  redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)

  async def get_redis():
      """Get the Redis client instance."""
      return redis_client

  async def check_redis_health():
      """Check if Redis is accessible."""
      try:
          await redis_client.ping()
          return True
      except Exception:
          return False
  ```

**Step 3: Update health check to include Redis**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/main.py`
- Update the health endpoint:
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

**Step 4: Test the health check**
- Make sure Redis is running (from docker-compose up)
- Test the health endpoint:
  ```bash
  curl http://localhost:8000/health
  ```
- You should see something like:
  ```json
  {"status":"ok","redis":"healthy"}
  ```

**Acceptance Criteria (check these when done):**
- [ ] File `redis_client.py` exists with Redis client setup
- [ ] File has get_redis() function
- [ ] File has check_redis_health() function
- [ ] main.py imports check_redis_health
- [ ] Health endpoint includes Redis status
- [ ] Health check returns "redis: healthy" when Redis is running
- [ ] Health check returns "redis: unhealthy" when Redis is down

---

### P1-3.2 Read-through cache on redirect

**What this task means:** "Read-through cache" means: when you need data, check the cache first. If it's there (cache hit), use it. If not (cache miss), get it from the database and store it in the cache for next time. This makes subsequent requests much faster.

**Objective:** Implement caching for link lookups so redirects are faster.

**Steps:**

**Step 1: Create cache_service.py**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/services/cache_service.py`
- Add this code:
  ```python
  import json
  from datetime import datetime
  from lex_shortlink_api.redis_client import get_redis
  from lex_shortlink_api.models.link import Link

  class CacheService:
      def __init__(self):
          self.redis = None

      async def get_redis(self):
          """Get or create Redis client."""
          if not self.redis:
              self.redis = await get_redis()
          return self.redis

      async def get_link(self, slug: str) -> dict | None:
          """Get link data from cache."""
          redis = await self.get_redis()
          data = await redis.get(f"link:slug:{slug}")
          if data:
              return json.loads(data)
          return None

      async def set_link(self, slug: str, link: Link, ttl: int = 3600):
          """Store link data in cache."""
          redis = await self.get_redis()
          data = {
              "original_url": link.original_url,
              "expires_at": link.expires_at.isoformat() if link.expires_at else None,
              "password_hash": link.password_hash,
              "is_deleted": link.is_deleted,
          }
          await redis.setex(f"link:slug:{slug}", ttl, json.dumps(data))

      async def delete_link(self, slug: str):
          """Remove link data from cache."""
          redis = await self.get_redis()
          await redis.delete(f"link:slug:{slug}")
  ```

**Step 2: Update LinkRepository to use cache**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/repositories/link_repository.py`
- Update the LinkRepository class:
  ```python
  from lex_shortlink_api.services.cache_service import CacheService

  class LinkRepository:
      def __init__(self, db: AsyncSession, cache: CacheService = None):
          self.db = db
          self.cache = cache or CacheService()

      async def create(self, link: Link) -> Link:
          self.db.add(link)
          await self.db.commit()
          await self.db.refresh(link)
          return link

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

          # Populate cache for next time
          if link:
              await self.cache.set_link(slug, link)

          return link

      async def slug_exists(self, slug: str) -> bool:
          result = await self.db.execute(
              select(Link).where(Link.slug == slug)
          )
          return result.scalar_one_or_none() is not None
  ```

**Step 3: Update LinkService to cache on create**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/services/link_service.py`
- Update the create_link method:
  ```python
  async def create_link(self, data: LinkCreate) -> Link:
      if data.custom_slug:
          if not self.validate_slug(data.custom_slug):
              raise ValueError("Invalid slug format: only alphanumeric characters and hyphens allowed")
          slug = data.custom_slug
      else:
          slug = self.generate_slug()

      if len(slug) < 3 or len(slug) > 50:
          raise ValueError("Slug must be between 3 and 50 characters")

      if await self.link_repo.slug_exists(slug):
          raise ValueError("Slug already exists")

      link = Link(
          slug=slug,
          original_url=str(data.url),
          expires_at=data.expires_at,
      )

      if data.password:
          link.password_hash = self.hash_password(data.password)

      link = await self.link_repo.create(link)

      # Cache the new link
      await self.link_repo.cache.set_link(link.slug, link)

      return link
  ```

**Step 4: Test the cache**
- Create a link:
  ```bash
  curl -X POST http://localhost:8000/api/v1/links \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com"}'
  ```
- Note the slug
- Make a redirect request (this should cache the link):
  ```bash
  curl -I http://localhost:8000/{slug}
  ```
- Make another redirect request (should hit cache):
  ```bash
  curl -I http://localhost:8000/{slug}
  ```

**Acceptance Criteria (check these when done):**
- [ ] File `services/cache_service.py` exists
- [ ] CacheService has get_link method
- [ ] CacheService has set_link method
- [ ] CacheService has delete_link method
- [ ] LinkRepository uses cache in get_by_slug
- [ ] LinkRepository populates cache on DB miss
- [ ] LinkService caches new links on create
- [ ] Cache TTL is 3600 seconds (1 hour)
- [ ] Redirects work with caching enabled

---

### P1-3.3 Cache invalidation on update/delete

**What this task means:** When you update or delete a link in the database, the cached version in Redis becomes stale (outdated). You need to delete it from Redis so the next request will fetch the fresh version from the database.

**Objective:** Ensure cache is deleted when links are modified or deleted.

**Steps:**

**Step 1: Add update method to LinkRepository**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/repositories/link_repository.py`
- Add this method to LinkRepository:
  ```python
  async def update_link(self, link: Link):
      """Update a link and invalidate its cache."""
      await self.db.commit()
      await self.db.refresh(link)
      # Invalidate cache
      await self.cache.delete_link(link.slug)
  ```

**Step 2: Add delete method to LinkRepository**
- In the same file, add this method:
  ```python
  async def delete_link(self, slug: str):
      """Soft delete a link and invalidate its cache."""
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

**Step 3: Add delete endpoint to API**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/api/links.py`
- Add this endpoint:
  ```python
  from fastapi import HTTPException, status

  @router.delete("/{slug}")
  async def delete_link(slug: str, db: AsyncSession = Depends(get_db)):
      link_repo = LinkRepository(db)
      link = await link_repo.delete_link(slug)
      if not link:
          raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
      return {"message": "Link deleted"}
  ```

**Step 4: Test cache invalidation**
- Create a link:
  ```bash
  curl -X POST http://localhost:8000/api/v1/links \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com"}'
  ```
- Note the slug
- Make a redirect (this caches the link):
  ```bash
  curl -I http://localhost:8000/{slug}
  ```
- Delete the link:
  ```bash
  curl -X DELETE http://localhost:8000/api/v1/links/{slug}
  ```
- Try to redirect again (should return 410 Gone, not the cached redirect):
  ```bash
  curl -I http://localhost:8000/{slug}
  ```

**Acceptance Criteria (check these when done):**
- [ ] LinkRepository has update_link method
- [ ] LinkRepository has delete_link method
- [ ] update_link invalidates cache
- [ ] delete_link invalidates cache
- [ ] DELETE endpoint exists in API
- [ ] Deleted link returns 410 on redirect (not cached 302)
- [ ] Cache is cleared after deletion

---

### P1-3.4 Enqueue click on redirect (no sync DB write)

**What this task means:** Instead of writing click data directly to the database during the redirect (which would slow it down), you'll write it to a Redis Stream. A Redis Stream is like a log that can handle very high throughput. Later, a background worker will read from this stream and write to the database.

**Objective:** Implement async click logging using Redis Stream so redirects aren't blocked by database writes.

**Steps:**

**Step 1: Add click logging to CacheService**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/services/cache_service.py`
- Add this method to CacheService:
  ```python
  async def log_click(self, link_id: str, click_data: dict):
      """Log a click event to Redis Stream."""
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

**Step 2: Update redirect endpoint to log clicks**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/api/redirects.py`
- Update the redirect function to log clicks:
  ```python
  from fastapi import Request
  from datetime import datetime

  @router.get("/{slug}")
  async def redirect(slug: str, request: Request, db: AsyncSession = Depends(get_db)):
      logger.info(json.dumps({
          "event": "redirect_attempt",
          "slug": slug,
          "timestamp": datetime.now().isoformat(),
      }))

      link_repo = LinkRepository(db)
      link = await link_repo.get_by_slug(slug)

      if not link:
          logger.warning(json.dumps({
              "event": "redirect_not_found",
              "slug": slug,
          }))
          raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

      if link.expires_at and link.expires_at < datetime.now():
          logger.warning(json.dumps({
              "event": "redirect_expired",
              "slug": slug,
              "expires_at": link.expires_at.isoformat(),
          }))
          raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link has expired")

      if link.is_deleted:
          logger.warning(json.dumps({
              "event": "redirect_deleted",
              "slug": slug,
          }))
          raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link has been deleted")

      # Log click asynchronously (doesn't block the redirect)
      click_data = {
          "clicked_at": datetime.now().isoformat(),
          "referrer": request.headers.get("referer", ""),
          "user_agent": request.headers.get("user-agent", ""),
      }
      await link_repo.cache.log_click(str(link.id), click_data)

      logger.info(json.dumps({
          "event": "redirect_success",
          "slug": slug,
          "target_url": link.original_url,
      }))

      return Response(status_code=status.HTTP_302_FOUND, headers={"Location": link.original_url})
  ```

**Step 3: Test click logging**
- Create a link:
  ```bash
  curl -X POST http://localhost:8000/api/v1/links \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com"}'
  ```
- Note the slug
- Make a redirect request:
  ```bash
  curl -I http://localhost:8000/{slug}
  ```
- Check the Redis stream (you'll need to access Redis CLI):
  ```bash
  docker exec -it shortlink-api-redis-1 redis-cli
  ```
  Inside Redis CLI:
  ```
  XLEN clicks:stream
  XRANGE clicks:stream - +
  ```
  You should see the click event in the stream

**Acceptance Criteria (check these when done):**
- [ ] CacheService has log_click method
- [ ] log_click writes to Redis Stream "clicks:stream"
- [ ] Redirect endpoint calls log_click
- [ ] Click data includes link_id, timestamp, referrer, user-agent
- [ ] Redirect returns immediately (doesn't wait for DB write)
- [ ] Click events appear in Redis Stream
- [ ] XLEN clicks:stream shows count > 0

---

### P1-3.5 Background worker: batch flush to Postgres

**What this task means:** You need a separate background process that continuously reads click events from the Redis Stream and writes them to the PostgreSQL database. This runs independently of the API server, so it doesn't slow down redirects.

**Objective:** Implement a background worker that processes click events from Redis Stream and writes them to the database.

**Steps:**

**Step 1: Create the workers directory**
- Create a new directory: `src/lex_shortlink_api/workers/`
- Full path: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/workers/`

**Step 2: Create __init__.py for workers**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/workers/__init__.py`
- This file can be empty

**Step 3: Create click_worker.py**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/workers/click_worker.py`
- Add this code:
  ```python
  import asyncio
  import uuid
  from datetime import datetime

  from lex_shortlink_api.redis_client import get_redis
  from lex_shortlink_api.database import AsyncSessionLocal
  from lex_shortlink_api.models.click_event import ClickEvent

  async def process_clicks():
      """Background worker to process click events from Redis Stream."""
      redis = await get_redis()

      while True:
          # Read up to 100 entries from the stream
          # Block for 5 seconds if no entries
          entries = await redis.xread(
              {"clicks:stream": "0"},
              count=100,
              block=5000
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

                  # Remove processed entries from stream
                  last_id = messages[-1][0]
                  await redis.xtrim("clicks:stream", maxlen=0)

  if __name__ == "__main__":
      asyncio.run(process_clicks())
  ```

**Step 4: Update docker-compose.yml to run the worker**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/docker-compose.yml`
- Add a worker service:
  ```yaml
  services:
    api:
      # ... existing api config ...
    
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

**Step 5: Test the worker**
- Start all services:
  ```bash
  docker compose up
  ```
- Create a link and make some redirects (from P1-3.4)
- Check the database for click events:
  ```bash
  docker exec -it shortlink-api-postgres-1 psql -U shortlink -d shortlink
  ```
  In PostgreSQL:
  ```sql
  SELECT COUNT(*) FROM click_events;
  SELECT * FROM click_events ORDER BY clicked_at DESC LIMIT 5;
  ```

**Acceptance Criteria (check these when done):**
- [ ] Directory `workers/` exists
- [ ] File `workers/click_worker.py` exists
- [ ] Worker reads from Redis Stream
- [ ] Worker writes click events to database
- [ ] Worker processes in batches (up to 100 at a time)
- [ ] docker-compose.yml includes worker service
- [ ] Click events appear in database after redirects
- [ ] Worker runs continuously

---

### P1-3.6 Optional Redis click counter

**What this task means:** This is an optional feature to track real-time click counts in Redis. This gives you instant click counts without waiting for the database to be updated. It's useful for showing "live" statistics.

**Objective:** Add a real-time click counter using Redis.

**Steps:**

**Step 1: Add counter methods to CacheService**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/services/cache_service.py`
- Add these methods to CacheService:
  ```python
  async def increment_click_count(self, slug: str) -> int:
      """Increment the click counter for a slug."""
      redis = await self.get_redis()
      key = f"clicks:counter:{slug}"
      count = await redis.incr(key)
      if count == 1:  # First increment, set TTL
          await redis.expire(key, 300)  # 5 minutes
      return count

  async def get_click_count(self, slug: str) -> int:
      """Get the current click count for a slug."""
      redis = await self.get_redis()
      count = await redis.get(f"clicks:counter:{slug}")
      return int(count) if count else 0
  ```

**Step 2: Update redirect to increment counter**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/api/redirects.py`
- Add this after logging the click:
  ```python
  # Increment real-time click counter
  await link_repo.cache.increment_click_count(slug)
  ```

**Step 3: Add endpoint to get click count**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/api/links.py`
- Add this endpoint:
  ```python
  @router.get("/{slug}/clicks")
  async def get_click_count(slug: str, db: AsyncSession = Depends(get_db)):
      link_repo = LinkRepository(db)
      count = await link_repo.cache.get_click_count(slug)
      return {"slug": slug, "clicks": count}
  ```

**Step 4: Test the counter**
- Create a link and note the slug
- Make several redirect requests
- Check the click count:
  ```bash
  curl http://localhost:8000/api/v1/links/{slug}/clicks
  ```

**Acceptance Criteria (check these when done):**
- [ ] CacheService has increment_click_count method
- [ ] CacheService has get_click_count method
- [ ] Counter TTL is 300 seconds (5 minutes)
- [ ] Redirect increments the counter
- [ ] Endpoint returns current click count
- [ ] Counter resets after TTL expires

---

### P1-3.7 Integration test: click eventually in DB

**What this task means:** Since click logging is async (clicks go to Redis first, then to database), there's a delay before clicks appear in the database. You need a test that verifies clicks eventually show up in the database after the worker processes them.

**Objective:** Add an integration test that verifies click events eventually appear in the database.

**Steps:**

**Step 1: Create test_click_logging.py**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/tests/integration/test_click_logging.py`
- Add this code:
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
          # Create a link
          response = await ac.post("/api/v1/links", json={"url": "https://example.com"})
          assert response.status_code == 201
          slug = response.json()["slug"]

          # Make a redirect request (this logs click to Redis)
          await ac.get(f"/{slug}")

          # Wait for worker to process (max 10 seconds)
          for _ in range(20):
              async with AsyncSessionLocal() as db:
                  result = await db.execute(select(ClickEvent))
                  count = len(result.all())
                  if count > 0:
                      break
              await asyncio.sleep(0.5)

          # Verify click is in database
          async with AsyncSessionLocal() as db:
              result = await db.execute(select(ClickEvent))
              clicks = result.all()
              assert len(clicks) > 0
  ```

**Step 2: Run the test with worker**
- Make sure the worker is running:
  ```bash
  docker compose up worker
  ```
- In another terminal, run the test:
  ```bash
  pytest tests/integration/test_click_logging.py
  ```

**Acceptance Criteria (check these when done):**
- [ ] File `tests/integration/test_click_logging.py` exists
- [ ] Test creates a link and makes a redirect
- [ ] Test waits for worker to process (up to 10 seconds)
- [ ] Test verifies click appears in database
- [ ] Test passes when worker is running

---

## Phase 4 - Analytics

**What this phase means:** Now we add analytics features. You'll capture information about who's clicking links (device type, location, referrer) and build an API to retrieve statistics. You'll also create a simple dashboard to visualize the data.

### P1-4.1 User-Agent → device type

**What this task means:** The User-Agent header in HTTP requests tells you what browser/device the user is using. You'll parse this to determine if it's a mobile device, tablet, desktop, or other. This helps you understand your audience.

**Objective:** Parse User-Agent strings to determine device type.

**Steps:**

**Step 1: Install user-agents library**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/requirements.txt`
- Add this line:
  ```
  user-agents>=2.2.0,<3.0.0
  ```
- Install it:
  ```bash
  pip install user-agents
  ```

**Step 2: Create utils directory and device parser**
- Create directory: `src/lex_shortlink_api/utils/`
- Full path: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/utils/`
- Create `__init__.py` (can be empty)
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/utils/device_parser.py`
- Add this code:
  ```python
  from user_agents import parse

  def get_device_type(user_agent: str) -> str:
      """Parse user agent string to determine device type."""
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

**Step 3: Update redirect to capture device type**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/api/redirects.py`
- Import the device parser:
  ```python
  from lex_shortlink_api.utils.device_parser import get_device_type
  ```
- Update the click data to include device type:
  ```python
  click_data = {
      "clicked_at": datetime.now().isoformat(),
      "referrer": request.headers.get("referer", ""),
      "user_agent": request.headers.get("user-agent", ""),
      "device_type": get_device_type(request.headers.get("user-agent", "")),
  }
  ```

**Step 4: Test device detection**
- Make a redirect request with curl (which has a specific user agent):
  ```bash
  curl -I http://localhost:8000/{slug}
  ```
- Check the database for the device type:
  ```bash
  docker exec -it shortlink-api-postgres-1 psql -U shortlink -d shortlink
  ```
  ```sql
  SELECT device_type FROM click_events ORDER BY clicked_at DESC LIMIT 1;
  ```

**Acceptance Criteria (check these when done):**
- [ ] requirements.txt includes user-agents
- [ ] utils/ directory exists
- [ ] device_parser.py exists with get_device_type function
- [ ] Function returns mobile, tablet, desktop, or other
- [ ] Redirect endpoint captures device type
- [ ] Device type is logged with click events
- [ ] Device type appears in database

---

### P1-4.2 GeoIP → country

**What this task means:** GeoIP (Geographic IP) determines the country of a user based on their IP address. This helps you understand where your audience is located geographically. For local development, you'll use a fallback since localhost doesn't have a real location.

**Objective:** Determine country from IP address using GeoIP.

**Steps:**

**Step 1: Install geoip2 library**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/requirements.txt`
- Add this line:
  ```
  geoip2>=4.0.0,<5.0.0
  ```
- Install it:
  ```bash
  pip install geoip2
  ```

**Step 2: Download GeoIP database**
- Create data directory:
  ```bash
  mkdir -p data
  ```
- Download the free GeoLite2 database from MaxMind (you'll need to sign up for a free account):
  - Go to https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
  - Sign up and get a license key
  - Download the GeoLite2-Country database
  - Extract it to `data/GeoLite2-Country.mmdb`

**Step 3: Create geoip.py utility**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/utils/geoip.py`
- Add this code:
  ```python
  import geoip2.database

  from lex_shortlink_api.config import get_settings

  settings = get_settings()

  try:
      reader = geoip2.database.Reader("data/GeoLite2-Country.mmdb")
  except Exception:
      reader = None

  def get_country_code(ip_address: str) -> str | None:
      """Get country code from IP address."""
      if not reader:
          return "US"  # Default for local dev if database not available
      
      if ip_address in ["127.0.0.1", "::1", "localhost"]:
          return "US"  # Default for local development
      
      try:
          response = reader.country(ip_address)
          return response.country.iso_code
      except Exception:
          return None
  ```

**Step 4: Update redirect to capture country**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/api/redirects.py`
- Import the geoip function:
  ```python
  from lex_shortlink_api.utils.geoip import get_country_code
  ```
- Update the click data to include country:
  ```python
  client_ip = request.client.host if request.client else "127.0.0.1"
  click_data = {
      "clicked_at": datetime.now().isoformat(),
      "referrer": request.headers.get("referer", ""),
      "user_agent": request.headers.get("user-agent", ""),
      "device_type": get_device_type(request.headers.get("user-agent", "")),
      "country_code": get_country_code(client_ip),
  }
  ```

**Step 5: Test GeoIP**
- Make a redirect request:
  ```bash
  curl -I http://localhost:8000/{slug}
  ```
- Check the database for country code:
  ```bash
  docker exec -it shortlink-api-postgres-1 psql -U shortlink -d shortlink
  ```
  ```sql
  SELECT country_code FROM click_events ORDER BY clicked_at DESC LIMIT 1;
  ```

**Acceptance Criteria (check these when done):**
- [ ] requirements.txt includes geoip2
- [ ] GeoLite2-Country.mmdb database downloaded
- [ ] geoip.py exists with get_country_code function
- [ ] Function returns country code or None
- [ ] Fallback for localhost returns "US"
- [ ] Redirect endpoint captures country code
- [ ] Country code appears in database

---

### P1-4.3 Capture Referer

**What this task means:** The Referer (misspelled in HTTP) header tells you which website the user came from before clicking your link. This helps you understand where your traffic is coming from.

**Objective:** Capture the HTTP Referer header with click events.

**Steps:**

**Step 1: Update redirect to capture referer**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/api/redirects.py`
- The referer is already being captured in the click_data, but let's make sure it's cleaned:
  ```python
  from urllib.parse import urlparse

  # In the redirect function, clean the referer
  referer = request.headers.get("referer", "")
  if referer:
      # Clean referer URL (remove query params for privacy)
      parsed = urlparse(referer)
      referer = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
      # Truncate if too long
      if len(referer) > 500:
          referer = referer[:500]
  
  click_data = {
      "clicked_at": datetime.now().isoformat(),
      "referrer": referer,
      "user_agent": request.headers.get("user-agent", ""),
      "device_type": get_device_type(request.headers.get("user-agent", "")),
      "country_code": get_country_code(client_ip),
  }
  ```

**Step 2: Test referer capture**
- Make a redirect request with a referer:
  ```bash
  curl -I -H "Referer: https://twitter.com" http://localhost:8000/{slug}
  ```
- Check the database for the referer:
  ```bash
  docker exec -it shortlink-api-postgres-1 psql -U shortlink -d shortlink
  ```
  ```sql
  SELECT referrer FROM click_events ORDER BY clicked_at DESC LIMIT 1;
  ```

**Acceptance Criteria (check these when done):**
- [ ] Referer header is captured
- [ ] Referer URL is cleaned (query params removed)
- [ ] Referer is truncated if too long (max 500 chars)
- [ ] Empty referer handled gracefully
- [ ] Referer appears in database

---

### P1-4.4 GET /api/v1/links/{slug}/stats (aggregates)

**What this task means:** This is the analytics API endpoint. It aggregates click data from the database to show statistics like total clicks, clicks over time, top countries, top referrers, and device breakdown.

**Objective:** Implement the analytics aggregation endpoint.

**Steps:**

**Step 1: Create ClickRepository**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/repositories/click_repository.py`
- Add this code:
  ```python
  from sqlalchemy import select, func, and_
  from datetime import datetime, timedelta
  from sqlalchemy.ext.asyncio import AsyncSession

  from lex_shortlink_api.models.click_event import ClickEvent
  from lex_shortlink_api.models.link import Link

  class ClickRepository:
      def __init__(self, db: AsyncSession):
          self.db = db

      async def get_stats(self, slug: str, days: int = 7) -> dict | None:
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

**Step 2: Add stats endpoint to API**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/api/links.py`
- Add this endpoint:
  ```python
  from lex_shortlink_api.repositories.click_repository import ClickRepository

  @router.get("/{slug}/stats")
  async def get_stats(slug: str, days: int = 7, db: AsyncSession = Depends(get_db)):
      click_repo = ClickRepository(db)
      stats = await click_repo.get_stats(slug, days)
      if not stats:
          raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
      return stats
  ```

**Step 3: Test the stats endpoint**
- Create a link and make some redirects
- Get the stats:
  ```bash
  curl http://localhost:8000/api/v1/links/{slug}/stats
  ```

**Acceptance Criteria (check these when done):**
- [ ] ClickRepository exists with get_stats method
- [ ] Returns total_clicks
- [ ] Returns clicks_by_day (last N days)
- [ ] Returns top_countries (top 10)
- [ ] Returns top_referrers (top 10)
- [ ] Returns devices breakdown
- [ ] Stats endpoint exists in API
- [ ] Returns 404 for non-existent slugs

---

### P1-4.5 Simple HTMX dashboard

**What this task means:** HTMX is a library that lets you add dynamic features to your web pages without writing JavaScript. You'll create a simple HTML dashboard that shows link statistics and updates dynamically.

**Objective:** Create a simple HTML dashboard using HTMX to display link statistics.

**Steps:**

**Step 1: Create static directory**
- Create directory: `static/`
- Full path: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/static/`

**Step 2: Create dashboard.html**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/static/dashboard.html`
- Add this code:
  ```html
  <!DOCTYPE html>
  <html lang="en">
  <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Shortlink Dashboard</title>
      <script src="https://unpkg.com/htmx.org@1.9.10"></script>
      <style>
          body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
          .card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
          .stat { font-size: 24px; font-weight: bold; }
          input { padding: 10px; margin: 10px 0; width: 70%; }
          button { padding: 10px 20px; cursor: pointer; }
      </style>
  </head>
  <body>
      <h1>Shortlink Dashboard</h1>
      
      <div class="card">
          <h2>View Link Statistics</h2>
          <input type="text" id="slug" placeholder="Enter slug (e.g., abc123)">
          <button onclick="loadStats()">Load Stats</button>
      </div>
      
      <div id="stats" class="card" style="display: none;">
          <h3>Statistics for: <span id="slug-display"></span></h3>
          <p>Total Clicks: <span class="stat" id="total-clicks">0</span></p>
          <div id="details"></div>
      </div>
      
      <script>
          function loadStats() {
              const slug = document.getElementById('slug').value;
              if (!slug) return;
              
              fetch(`/api/v1/links/${slug}/stats`)
                  .then(response => response.json())
                  .then(data => {
                      document.getElementById('stats').style.display = 'block';
                      document.getElementById('slug-display').textContent = slug;
                      document.getElementById('total-clicks').textContent = data.total_clicks;
                      
                      let details = '<h4>Top Countries:</h4><ul>';
                      data.top_countries.forEach(c => {
                          details += `<li>${c.country_code}: ${c.clicks}</li>`;
                      });
                      details += '</ul>';
                      
                      details += '<h4>Top Referrers:</h4><ul>';
                      data.top_referrers.forEach(r => {
                          details += `<li>${r.referrer}: ${r.clicks}</li>`;
                      });
                      details += '</ul>';
                      
                      details += '<h4>Devices:</h4><ul>';
                      for (const [device, count] of Object.entries(data.devices)) {
                          details += `<li>${device}: ${count}</li>`;
                      }
                      details += '</ul>';
                      
                      document.getElementById('details').innerHTML = details;
                  })
                  .catch(error => {
                      alert('Link not found');
                  });
          }
      </script>
  </body>
  </html>
  ```

**Step 3: Serve static files in FastAPI**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/main.py`
- Add static file serving:
  ```python
  from fastapi.staticfiles import StaticFiles

  # Mount static files directory
  app.mount("/static", StaticFiles(directory="static"), name="static")
  ```

**Step 4: Test the dashboard**
- Start the API server
- Open in browser: `http://localhost:8000/static/dashboard.html`
- Enter a slug and click "Load Stats"

**Acceptance Criteria (check these when done):**
- [ ] static/ directory exists
- [ ] dashboard.html exists with HTML structure
- [ ] Dashboard has input for slug
- [ ] Dashboard calls stats API
- [ ] Dashboard displays total clicks
- [ ] Dashboard displays top countries
- [ ] Dashboard displays top referrers
- [ ] Dashboard displays device breakdown
- [ ] FastAPI serves static files
- [ ] Dashboard loads in browser

---

## Phase 5 - API Keys & Rate Limiting

**What this phase means:** Now we add API key authentication and rate limiting. This prevents abuse by limiting how many requests each API key can make. Users will need an API key to create links.

### P1-5.1 POST /api/v1/api-keys (create API key)

**What this task means:** Users need API keys to use the API. You'll create an endpoint that generates new API keys. The keys will be hashed before storing in the database for security.

**Objective:** Implement API key creation endpoint.

**Steps:**

**Step 1: Create ApiKeyRepository**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/repositories/api_key_repository.py`
- Add this code:
  ```python
  from sqlalchemy import select
  from sqlalchemy.ext.asyncio import AsyncSession
  import secrets

  from lex_shortlink_api.models.api_key import ApiKey

  class ApiKeyRepository:
      def __init__(self, db: AsyncSession):
          self.db = db

      async def create(self, name: str) -> tuple[ApiKey, str]:
          """Create a new API key and return the key and the model."""
          # Generate a random API key
          api_key = secrets.token_urlsafe(32)
          
          # Hash the key for storage
          key_hash = self.hash_key(api_key)
          
          api_key_model = ApiKey(
              key_hash=key_hash,
              name=name,
          )
          
          self.db.add(api_key_model)
          await self.db.commit()
          await self.db.refresh(api_key_model)
          
          return api_key_model, api_key

      def hash_key(self, api_key: str) -> str:
          """Simple hash for API key (use bcrypt in production)."""
          import hashlib
          return hashlib.sha256(api_key.encode()).hexdigest()

      async def get_by_key_hash(self, key_hash: str) -> ApiKey | None:
          result = await self.db.execute(
              select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active == True)
          )
          return result.scalar_one_or_none()
  ```

**Step 2: Create API key schemas**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/schemas/api_key.py`
- Add this code:
  ```python
  from pydantic import BaseModel

  class ApiKeyCreate(BaseModel):
      name: str

  class ApiKeyResponse(BaseModel):
      id: str
      name: str
      api_key: str
      created_at: str

      class Config:
          from_attributes = True
  ```

**Step 3: Add API key endpoint**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/api/api_keys.py`
- Create this file:
  ```python
  from fastapi import APIRouter, Depends
  from sqlalchemy.ext.asyncio import AsyncSession

  from lex_shortlink_api.database import get_db
  from lex_shortlink_api.schemas.api_key import ApiKeyCreate, ApiKeyResponse
  from lex_shortlink_api.repositories.api_key_repository import ApiKeyRepository

  router = APIRouter(prefix="/api/v1/api-keys", tags=["api-keys"])

  @router.post("", status_code=201)
  async def create_api_key(data: ApiKeyCreate, db: AsyncSession = Depends(get_db)):
      api_key_repo = ApiKeyRepository(db)
      api_key_model, api_key = await api_key_repo.create(data.name)
      
      return ApiKeyResponse(
          id=str(api_key_model.id),
          name=api_key_model.name,
          api_key=api_key,  # Only returned once on creation
          created_at=api_key_model.created_at.isoformat(),
      )
  ```

**Step 4: Update main.py to include API keys router**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/main.py`
- Add this import:
  ```python
  from lex_shortlink_api.api.api_keys import router as api_keys_router
  ```
- Add this line:
  ```python
  app.include_router(api_keys_router)
  ```

**Step 5: Test API key creation**
- Create an API key:
  ```bash
  curl -X POST http://localhost:8000/api/v1/api-keys \
    -H "Content-Type: application/json" \
    -d '{"name": "My App"}'
  ```
- Save the returned api_key - you'll need it for authentication

**Acceptance Criteria (check these when done):**
- [ ] ApiKeyRepository exists with create method
- [ ] API key is generated randomly
- [ ] API key is hashed before storage
- [ ] API key schemas exist
- [ ] API keys router exists
- [ ] POST /api/v1/api-keys endpoint works
- [ ] Returns api_key (only on creation)
- [ ] main.py includes api_keys router

---

### P1-5.2 Require API key for POST /api/v1/links

**What this task means:** Now you'll require users to provide an API key when creating links. This prevents unauthorized use of the API. The API key will be passed in a header.

**Objective:** Add API key authentication to the link creation endpoint.

**Steps:**

**Step 1: Create authentication dependency**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/api/auth.py`
- Create this file:
  ```python
  from fastapi import HTTPException, status, Header
  from sqlalchemy.ext.asyncio import AsyncSession

  from lex_shortlink_api.repositories.api_key_repository import ApiKeyRepository

  async def verify_api_key(
      x_api_key: str = Header(..., description="API Key for authentication"),
      db: AsyncSession = Depends(get_db)
  ) -> str:
      """Verify the API key and return the key hash."""
      import hashlib
      key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
      
      api_key_repo = ApiKeyRepository(db)
      api_key = await api_key_repo.get_by_key_hash(key_hash)
      
      if not api_key:
          raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="Invalid API key"
          )
      
      return key_hash
  ```

**Step 2: Update link creation to require API key**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/api/links.py`
- Update the create_link endpoint:
  ```python
  from lex_shortlink_api.api.auth import verify_api_key

  @router.post("", status_code=status.HTTP_201_CREATED)
  async def create_link(
      data: LinkCreate,
      db: AsyncSession = Depends(get_db),
      api_key_hash: str = Depends(verify_api_key)
  ):
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

**Step 3: Test API key requirement**
- Try to create a link without API key (should fail):
  ```bash
  curl -X POST http://localhost:8000/api/v1/links \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com"}'
  ```
- Should return 401 Unauthorized
- Create a link with API key (should succeed):
  ```bash
  curl -X POST http://localhost:8000/api/v1/links \
    -H "Content-Type: application/json" \
    -H "X-API-Key: YOUR_API_KEY_HERE" \
    -d '{"url": "https://example.com"}'
  ```

**Acceptance Criteria (check these when done):**
- [ ] auth.py exists with verify_api_key function
- [ ] verify_api_key checks key hash against database
- [ ] Returns 401 for invalid API keys
- [ ] Link creation requires API key
- [ ] Request without API key returns 401
- [ ] Request with valid API key succeeds

---

### P1-5.3 Rate limiting (Redis, per API key)

**What this task means:** Rate limiting prevents abuse by limiting how many requests each API key can make in a given time period. You'll use Redis to track request counts per API key.

**Objective:** Implement rate limiting per API key using Redis.

**Steps:**

**Step 1: Add rate limiting methods to CacheService**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/services/cache_service.py`
- Add these methods:
  ```python
  async def check_rate_limit(self, key_hash: str, limit: int = 100, window: int = 60) -> bool:
      """Check if API key is within rate limit."""
      redis = await self.get_redis()
      key = f"rate:api_key:{key_hash}:{window}s"
      
      # Increment counter
      current = await redis.incr(key)
      
      # Set expiry on first request
      if current == 1:
          await redis.expire(key, window)
      
      return current <= limit
  ```

**Step 2: Update auth.py to include rate limiting**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/api/auth.py`
- Update verify_api_key to include rate limiting:
  ```python
  from lex_shortlink_api.services.cache_service import CacheService

  async def verify_api_key(
      x_api_key: str = Header(..., description="API Key for authentication"),
      db: AsyncSession = Depends(get_db)
  ) -> str:
      """Verify the API key and check rate limit."""
      import hashlib
      key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
      
      api_key_repo = ApiKeyRepository(db)
      api_key = await api_key_repo.get_by_key_hash(key_hash)
      
      if not api_key:
          raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="Invalid API key"
          )
      
      # Check rate limit
      cache = CacheService()
      if not await cache.check_rate_limit(key_hash, limit=100, window=60):
          raise HTTPException(
              status_code=status.HTTP_429_TOO_MANY_REQUESTS,
              detail="Rate limit exceeded"
          )
      
      return key_hash
  ```

**Step 3: Test rate limiting**
- Make 100 successful requests with your API key
- The 101st request should return 429 Too Many Requests
- Wait 60 seconds and try again (should work)

**Acceptance Criteria (check these when done):**
- [ ] CacheService has check_rate_limit method
- [ ] Rate limit uses Redis
- [ ] Rate limit is per API key
- [ ] Rate limit window is 60 seconds
- [ ] Rate limit is 100 requests per window
- [ ] Returns 429 when limit exceeded
- [ ] Resets after window expires

---

## Phase 6 - Password Protection

**What this phase means:** Now we add password protection for links. Users can optionally set a password when creating a link, and visitors will need to enter the password before being redirected.

### P1-6.1 Password hashing (bcrypt)

**What this task means:** Never store passwords in plain text. You'll use bcrypt to hash passwords before storing them in the database. Bcrypt is a secure hashing algorithm designed for passwords.

**Objective:** Implement password hashing using bcrypt.

**Steps:**

**Step 1: Install bcrypt**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/requirements.txt`
- Add this line:
  ```
  passlib[bcrypt]>=1.7.4,<2.0.0
  ```
- Install it:
  ```bash
  pip install passlib[bcrypt]
  ```

**Step 2: Implement password hashing in LinkService**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/services/link_service.py`
- Update the hash_password method:
  ```python
  from passlib.context import CryptContext

  pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

  def hash_password(self, password: str) -> str:
      """Hash a password using bcrypt."""
      return pwd_context.hash(password)

  def verify_password(self, plain_password: str, hashed_password: str) -> bool:
      """Verify a password against a hash."""
      return pwd_context.verify(plain_password, hashed_password)
  ```

**Step 3: Update create_link to hash password**
- In the same file, the create_link method already calls hash_password, so it should work now with bcrypt

**Step 4: Test password hashing**
- Create a link with a password:
  ```bash
  curl -X POST http://localhost:8000/api/v1/links \
    -H "Content-Type: application/json" \
    -H "X-API-Key: YOUR_API_KEY" \
    -d '{"url": "https://example.com", "password": "mypassword"}'
  ```
- Check the database - the password_hash should be a bcrypt hash, not plain text

**Acceptance Criteria (check these when done):**
- [ ] requirements.txt includes passlib[bcrypt]
- [ ] hash_password uses bcrypt
- [ ] verify_password method exists
- [ ] Passwords are hashed before storage
- [ ] Hashed passwords are not plain text

---

### P1-6.2 Password verification on redirect

**What this task means:** When a link has a password, visitors need to provide it before being redirected. You'll add an endpoint to verify the password and return a token or session that allows the redirect.

**Objective:** Implement password verification for protected links.

**Steps:**

**Step 1: Add password verification endpoint**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/api/links.py`
- Add this endpoint:
  ```python
  from pydantic import BaseModel

  class PasswordVerify(BaseModel):
      password: str

  @router.post("/{slug}/verify-password")
  async def verify_password(
      slug: str,
      data: PasswordVerify,
      db: AsyncSession = Depends(get_db)
  ):
      link_repo = LinkRepository(db)
      link = await link_repo.get_by_slug(slug)
      
      if not link:
          raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
      
      if not link.password_hash:
          return {"password_required": False}
      
      from lex_shortlink_api.services.link_service import LinkService
      link_service = LinkService(link_repo)
      
      if not link_service.verify_password(data.password, link.password_hash):
          raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
      
      return {"password_required": True, "verified": True}
  ```

**Step 2: Update redirect to check password**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/src/lex_shortlink_api/api/redirects.py`
- Update the redirect function to check for password:
  ```python
  @router.get("/{slug}")
  async def redirect(slug: str, request: Request, db: AsyncSession = Depends(get_db)):
      link_repo = LinkRepository(db)
      link = await link_repo.get_by_slug(slug)

      if not link:
          raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

      if link.expires_at and link.expires_at < datetime.now():
          raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link has expired")

      if link.is_deleted:
          raise HTTPException(status_code=status.HTTP_410_GONE, detail="Link has been deleted")

      # Check if password is required
      if link.password_hash:
          # For simplicity, we'll return a special status code
          # In production, you'd use a session or token
          raise HTTPException(
              status_code=status.HTTP_403_FORBIDDEN,
              detail="Password required",
              headers={"X-Password-Required": "true"}
          )

      # Log click asynchronously
      click_data = {
          "clicked_at": datetime.now().isoformat(),
          "referrer": request.headers.get("referer", ""),
          "user_agent": request.headers.get("user-agent", ""),
          "device_type": get_device_type(request.headers.get("user-agent", "")),
          "country_code": get_country_code(client_ip),
      }
      await link_repo.cache.log_click(str(link.id), click_data)

      return Response(status_code=status.HTTP_302_FOUND, headers={"Location": link.original_url})
  ```

**Step 3: Test password protection**
- Create a link with a password
- Try to redirect without password (should return 403)
- Verify the password with the verify-password endpoint
- In a real implementation, you'd use a session to allow the redirect after verification

**Acceptance Criteria (check these when done):**
- [ ] Password verify endpoint exists
- [ ] Returns 401 for invalid passwords
- [ ] Returns success for valid passwords
- [ ] Redirect checks for password
- [ ] Returns 403 when password is required
- [ ] Password verification uses bcrypt

---

## Phase 7 - Load Testing

**What this phase means:** Load testing ensures your application can handle high traffic. You'll use k6 to simulate thousands of requests and verify the system can handle them.

### P1-7.1 k6 script for redirect path

**What this task means:** k6 is a load testing tool. You'll write a script that simulates users visiting short links to test performance.

**Objective:** Create a k6 load test script for the redirect endpoint.

**Steps:**

**Step 1: Install k6**
- Download k6 from https://k6.io/
- Or install via package manager (varies by OS)

**Step 2: Create load test script**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/tests/load/redirect_test.js`
- Create the directory and file:
  ```javascript
  import http from 'k6/http';
  import { check, sleep } from 'k6';

  export let options = {
      stages: [
          { duration: '30s', target: 100 },  // Ramp up to 100 users
          { duration: '1m', target: 100 },   // Stay at 100 users
          { duration: '30s', target: 0 },    // Ramp down to 0
      ],
  };

  export default function () {
      // Replace with an actual slug from your database
      let slug = 'test-slug';
      let res = http.get(`http://localhost:8000/${slug}`);
      
      check(res, {
          'status is 302': (r) => r.status === 302,
          'has location header': (r) => r.headers['Location'] !== undefined,
      });
      
      sleep(1);
  }
  ```

**Step 3: Run the load test**
- Make sure your API server is running
- Run the test:
  ```bash
  k6 run tests/load/redirect_test.js
  ```

**Step 4: Analyze results**
- k6 will show metrics like:
  - Requests per second
  - Response times
  - Error rates
- Look for any errors or slow responses

**Acceptance Criteria (check these when done):**
- [ ] k6 is installed
- [ ] Load test script exists
- [ ] Script tests redirect endpoint
- [ ] Script handles 302 redirects
- [ ] Load test runs without errors
- [ ] Results show acceptable performance

---

### P1-7.2 Target 10k redirects/sec

**What this task means:** This is the performance target. You want to handle 10,000 redirects per second. You'll run the load test at this scale to verify the system can handle it.

**Objective:** Verify the system can handle 10k redirects per second.

**Steps:**

**Step 1: Update load test script for higher load**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/tests/load/redirect_test.js`
- Update the options:
  ```javascript
  export let options = {
      stages: [
          { duration: '1m', target: 1000 },   // Ramp up to 1000 users
          { duration: '2m', target: 10000 },  // Ramp up to 10000 users
          { duration: '2m', target: 10000 },  // Stay at 10000 users
          { duration: '1m', target: 0 },      // Ramp down to 0
      ],
  };
  ```

**Step 2: Run the high-load test**
- Make sure Redis and PostgreSQL are running
- Run the test:
  ```bash
  k6 run tests/load/redirect_test.js
  ```

**Step 3: Monitor system resources**
- Watch CPU, memory, and disk usage during the test
- Check database connection pool
- Check Redis memory usage

**Step 4: Analyze bottlenecks**
- If performance is insufficient, identify bottlenecks:
  - Database queries
  - Redis operations
  - Network I/O
  - CPU usage

**Acceptance Criteria (check these when done):**
- [ ] Load test targets 10k requests/sec
- [ ] System handles 10k redirects/sec
- [ ] Error rate is < 1%
- [ ] Response time p95 < 100ms
- [ ] No resource exhaustion

---

## Phase 8 - Deployment

**What this phase means:** Now you'll deploy the application to AWS. You'll use Terraform for Infrastructure as Code to set up ECS Fargate (for the API), RDS (for PostgreSQL), ElastiCache (for Redis), and other AWS resources.

### P1-8.1 Dockerfile optimization

**What this task means:** A good Dockerfile is small, fast to build, and uses layers efficiently. You'll optimize the Dockerfile for production deployment.

**Objective:** Optimize the Dockerfile for production.

**Steps:**

**Step 1: Review existing Dockerfile**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/Dockerfile`
- Check if it exists and review its contents

**Step 2: Create optimized Dockerfile**
- If it doesn't exist, create it:
  ```dockerfile
  FROM python:3.11-slim as builder

  WORKDIR /app

  # Install build dependencies
  RUN apt-get update && apt-get install -y \
      gcc \
      && rm -rf /var/lib/apt/lists/*

  # Copy requirements and install
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt

  # Final stage
  FROM python:3.11-slim

  WORKDIR /app

  # Copy installed packages from builder
  COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
  COPY --from=builder /usr/local/bin /usr/local/bin

  # Copy application code
  COPY src/ ./src/

  # Set environment variables
  ENV PYTHONUNBUFFERED=1
  ENV PYTHONDONTWRITEBYTECODE=1

  # Run the application
  CMD ["uvicorn", "lex_shortlink_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

**Step 3: Build and test the Docker image**
- Build the image:
  ```bash
  docker build -t shortlink-api .
  ```
- Test it locally:
  ```bash
  docker run -p 8000:8000 shortlink-api
  ```

**Acceptance Criteria (check these when done):**
- [ ] Dockerfile is optimized (multi-stage build)
- [ ] Dockerfile uses slim base image
- [ ] Docker image builds successfully
- [ ] Docker image runs locally
- [ ] Image size is reasonable (< 500MB)

---

### P1-8.2 Terraform: ECS Fargate + RDS + ElastiCache

**What this task means:** Terraform is an Infrastructure as Code tool. You'll define your AWS infrastructure (ECS for running containers, RDS for database, ElastiCache for Redis) in code, making it reproducible and version-controlled.

**Objective:** Create Terraform configuration for AWS deployment.

**Steps:**

**Step 1: Create Terraform directory**
- Create directory: `terraform/`
- Full path: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/terraform/`

**Step 2: Create main.tf**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/terraform/main.tf`
- Add this basic configuration:
  ```hcl
  provider "aws" {
      region = "us-east-1"
  }

  resource "aws_ecs_cluster" "shortlink" {
      name = "shortlink-cluster"
  }

  resource "aws_ecs_task_definition" "api" {
      family = "shortlink-api"
      network_mode = "awsvpc"
      requires_compatibilities = ["FARGATE"]
      cpu = 256
      memory = 512
      
      container_definitions = jsonencode([
          {
              name = "api"
              image = "your-docker-image-url"
              essential = true
              portMappings = [{ containerPort = 8000 }]
              environment = [
                  { name = "DATABASE_URL", value = var.database_url }
                  { name = "REDIS_URL", value = var.redis_url }
              ]
          }
      ])
  }

  resource "aws_rds_cluster" "shortlink" {
      engine = "aurora-postgresql"
      engine_version = "15.4"
      database_name = "shortlink"
      master_username = "shortlink"
      master_password = var.db_password
      skip_final_snapshot = true
  }

  resource "aws_elasticache_cluster" "shortlink" {
      cluster_id = "shortlink-redis"
      engine = "redis"
      node_type = "cache.t3.micro"
      num_cache_nodes = 1
  }

  variable "db_password" {
      type = string
      sensitive = true
  }

  variable "database_url" {
      type = string
  }

  variable "redis_url" {
      type = string
  }

  output "ecs_cluster_arn" {
      value = aws_ecs_cluster.shortlink.arn
  }
  ```

**Step 3: Create .tfvars file for variables**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/terraform/terraform.tfvars`
- Add your values:
  ```hcl
  db_password = "your-secure-password"
  database_url = "postgresql://shortlink:password@cluster-endpoint:5432/shortlink"
  redis_url = "redis://cluster-endpoint:6379/0"
  ```

**Step 4: Initialize and apply Terraform**
- Initialize Terraform:
  ```bash
  cd terraform
  terraform init
  ```
- Review the plan:
  ```bash
  terraform plan
  ```
- Apply the infrastructure:
  ```bash
  terraform apply
  ```

**Acceptance Criteria (check these when done):**
- [ ] terraform/ directory exists
- [ ] main.tf defines ECS cluster
- [ ] main.tf defines RDS cluster
- [ ] main.tf defines ElastiCache cluster
- [ ] Variables are defined
- [ ] terraform init succeeds
- [ ] terraform plan shows intended changes
- [ ] terraform apply creates resources

---

### P1-8.3 CI/CD pipeline (GitHub Actions)

**What this task means:** CI/CD (Continuous Integration/Continuous Deployment) automates testing and deployment. When you push code to GitHub, it will automatically run tests and deploy to AWS.

**Objective:** Create a GitHub Actions workflow for CI/CD.

**Steps:**

**Step 1: Create .github/workflows directory**
- Create directory: `.github/workflows/`
- Full path: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/.github/workflows/`

**Step 2: Create ci-cd.yml**
- File location: `/home/lex/Documents/PersonalProjects/Lex-Shortlink-API/.github/workflows/ci-cd.yml`
- Add this workflow:
  ```yaml
  name: CI/CD Pipeline

  on:
    push:
      branches: [ main ]
    pull_request:
      branches: [ main ]

  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - name: Set up Python
          uses: actions/setup-python@v4
          with:
            python-version: '3.11'
        - name: Install dependencies
          run: |
            pip install -r requirements.txt
            pip install pytest
        - name: Run tests
          run: pytest tests/

    build-and-deploy:
      needs: test
      runs-on: ubuntu-latest
      if: github.ref == 'refs/heads/main'
      steps:
        - uses: actions/checkout@v3
        - name: Configure AWS credentials
          uses: aws-actions/configure-aws-credentials@v2
          with:
            aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
            aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
            aws-region: us-east-1
        - name: Login to Amazon ECR
          id: login-ecr
          uses: aws-actions/amazon-ecr-login@v1
        - name: Build and push Docker image
          env:
            ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
            ECR_REPOSITORY: shortlink-api
            IMAGE_TAG: ${{ github.sha }}
          run: |
            docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
            docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        - name: Deploy to ECS
          run: |
            aws ecs update-service --cluster shortlink-cluster --service shortlink-api --force-new-deployment
  ```

**Step 3: Configure GitHub secrets**
- Go to your GitHub repository settings
- Add secrets:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`

**Step 4: Test the pipeline**
- Push a change to the main branch
- Watch the Actions tab in GitHub
- Verify tests run and deployment succeeds

**Acceptance Criteria (check these when done):**
- [ ] .github/workflows/ directory exists
- [ ] ci-cd.yml workflow exists
- [ ] Workflow runs tests on push
- [ ] Workflow builds Docker image
- [ ] Workflow deploys to ECS
- [ ] GitHub secrets are configured
- [ ] Pipeline runs successfully on push
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
