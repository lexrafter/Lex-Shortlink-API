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