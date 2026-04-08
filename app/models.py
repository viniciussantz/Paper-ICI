import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, func, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/myapp"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Base(DeclarativeBase):
    pass

class Service(Base):
    __tablename__ = "services"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column()
    orgao: Mapped[str | None] = mapped_column()
    markdown_content: Mapped[str] = mapped_column()
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime | None] = mapped_column(server_default=func.now())
    
    chunks: Mapped[list["ServiceChunk"]] = relationship(back_populates="service", cascade="all, delete-orphan")

class ServiceChunk(Base):
    __tablename__ = "service_chunks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    service_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"))
    content: Mapped[str] = mapped_column()
    chunk_index: Mapped[int] = mapped_column()
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024))
    
    service: Mapped["Service"] = relationship(back_populates="chunks")
