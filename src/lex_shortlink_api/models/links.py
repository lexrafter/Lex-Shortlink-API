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