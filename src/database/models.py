"""
SQLAlchemy ORM models for RAG knowledge base
"""
from datetime import datetime
from typing import List
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class Document(Base):
    """Document model representing a source file"""
    __tablename__ = "documents"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String, nullable=True)
    total_chunks: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationship to chunks (with cascade delete)
    chunks: Mapped[List["Chunk"]] = relationship(
        "Chunk",
        back_populates="document_processing",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_documents_active', 'active'),
        Index('idx_documents_title', 'title'),
    )
    
    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title}', chunks={self.total_chunks})>"


class Chunk(Base):
    """Chunk model representing a text chunk from a document_processing"""
    __tablename__ = "chunks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    start_page: Mapped[int] = mapped_column(Integer, nullable=True)
    end_page: Mapped[int] = mapped_column(Integer, nullable=True)
    chunk_number: Mapped[int] = mapped_column(Integer, nullable=True)
    unit_name: Mapped[str] = mapped_column(String, default="page")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationship to document_processing
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
    
    # Index
    __table_args__ = (
        Index('idx_chunks_document', 'document_id'),
    )
    
    def __repr__(self):
        return f"<Chunk(id={self.id}, document_id={self.document_id}, pages={self.start_page}-{self.end_page})>"
