from sqlalchemy import Column, String, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base


class ReferenceDocument(Base):
    """
    Stores reference document links used in charter page.
    Each update creates a new row to maintain version history.
    """

    __tablename__ = "reference_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    document_code = Column(
        String,
        nullable=False,
        doc="Identifier of the document (PM_LITE, FULL_S9, PILM, PAR)"
    )

    document_name = Column(
        String,
        nullable=False,
        doc="Name displayed as hyperlink in charter page"
    )

    document_url = Column(
        Text,
        nullable=False,
        doc="URL of the document"
    )

    version = Column(
        Integer,
        nullable=False,
        doc="Version of the document link"
    )

    created_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        doc="User who created or updated the document"
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        doc="Timestamp when the record was created"
    )
