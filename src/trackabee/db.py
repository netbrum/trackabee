from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

engine = create_async_engine("sqlite+aiosqlite:///trackabee.db")

Session = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)
