import asyncio
from typing import AsyncGenerator

from fastapi import FastAPI, Depends
from sqlalchemy import String, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 1. Use an async driver (sqlite+aiosqlite)
DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# 2. Create the Async Engine
engine = create_async_engine(DATABASE_URL, echo=True)

# 3. Create an Async Session Factory
async_session_maker = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True)

app = FastAPI()

# --- Async Dependency ---

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async dependency for database sessions.
    FastAPI supports 'async def' dependencies natively.
    """
    async with async_session_maker() as session:
        yield session
        # session.commit() or rollback() happens here if needed, 
        # but 'async with' handles closure automatically.

# --- Async Endpoints ---

@app.get("/users/")
async def read_users(db: AsyncSession = Depends(get_async_db)):
    # In async mode, you MUST use the select() syntax
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users

@app.post("/users/")
async def create_user(email: str, db: AsyncSession = Depends(get_async_db)):
    new_user = User(email=email)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)