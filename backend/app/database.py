from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

raw_url = settings.DATABASE_URL

# Translate sync drivers to async equivalents
if raw_url.startswith("postgresql://"):
    DATABASE_URL = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif raw_url.startswith("sqlite:///"):
    DATABASE_URL = raw_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
else:
    DATABASE_URL = raw_url

is_sqlite = "sqlite" in DATABASE_URL
is_postgres = "postgresql" in DATABASE_URL

# Build connect args for SSL when on Postgres
# asyncpg uses different keywords than psycopg2 (sslmode/channel_binding aren't supported)
connect_args = {}
if is_postgres:
    parsed = urlparse(DATABASE_URL)
    qs = parse_qs(parsed.query)
    # Translate sslmode -> ssl
    sslmode = qs.pop("sslmode", [None])[0]
    qs.pop("channel_binding", None)  # asyncpg ignores this
    if sslmode in ("require", "verify-ca", "verify-full"):
        connect_args["ssl"] = True
    # Rebuild URL without the unsupported params
    DATABASE_URL = urlunparse(
        parsed._replace(query=urlencode({k: v[0] for k, v in qs.items()}))
    )

engine_kwargs = {"echo": settings.DEBUG, "pool_pre_ping": True}
if not is_sqlite:
    engine_kwargs.update({"pool_size": 5, "max_overflow": 10})
if connect_args:
    engine_kwargs["connect_args"] = connect_args

engine = create_async_engine(DATABASE_URL, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
