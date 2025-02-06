from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

DATABASE_URL = settings.database_uri

# The engine manages the connection pool, handles the communications with your database,.
engine = create_async_engine(DATABASE_URL, echo=True)  # echo=True will log all SQL statements

# Sessions are the main way you interact with your ORM-mapped models and the database.
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# The Base serves as the foundation for your database schema.
Base = declarative_base()
