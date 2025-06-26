from sqlalchemy import create_engine, MetaData, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings
import re
import json

# Database type compatibility layer
def get_database_types():
    """Return appropriate database types based on the database URL."""
    is_sqlite = "sqlite" in settings.DATABASE_URL.lower()
    
    if is_sqlite:
        # SQLite compatible types
        class UUID(String):
            """SQLite-compatible UUID type that stores UUIDs as strings."""
            def __init__(self, *args, **kwargs):
                self.as_uuid = kwargs.pop('as_uuid', True)
                length = kwargs.pop('length', 36)
                super().__init__(length, *args, **kwargs)
            def bind_processor(self, dialect):
                def process(value):
                    if value is not None:
                        return str(value)
                    return value
                return process
        
        class JSONB(Text):
            """SQLite-compatible JSONB type that stores JSON as text."""
            def bind_processor(self, dialect):
                def process(value):
                    if value is not None:
                        return json.dumps(value)
                    return value
                return process
            
            def result_processor(self, dialect, coltype):
                def process(value):
                    if value is not None:
                        return json.loads(value)
                    return value
                return process
            
    else:
        # PostgreSQL types
        from sqlalchemy.dialects.postgresql import UUID, JSONB
        UUIDType = UUID
        JSONBType = JSONB
    
    return UUID, JSONB

# Get the appropriate types for the current database
UUID, JSONB = get_database_types()

# Sync database engine and session (for migrations and non-async operations)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=0,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async database engine and session (for main application)
async_engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Metadata and Base class for models
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)

Base = declarative_base(metadata=metadata)


# Dependency to get async database session
async def get_async_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Dependency to get sync database session (for background tasks)
def get_sync_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Async context manager for database operations
class AsyncDatabaseManager:
    def __init__(self):
        self.session: AsyncSession = None
    
    async def __aenter__(self):
        self.session = AsyncSessionLocal()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type:
                await self.session.rollback()
            else:
                await self.session.commit()
            await self.session.close()


# Helper function to create all tables (used in startup)
async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Helper function to drop all tables (used in testing)
async def drop_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)