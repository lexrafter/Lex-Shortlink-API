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