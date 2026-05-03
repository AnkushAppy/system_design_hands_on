from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
from typing import Generator

# 1. Setup the Engine
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} # Needed only for SQLite
)

# 2. Modern Session Configuration
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. New SQLAlchemy 2.0 Base Class
class Base(DeclarativeBase):
    pass

# 4. Modern Declarative Mapping
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- Dependencies ---

def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a session. 
    FastAPI handles the cleanup (closing) after the yield.
    """
    with SessionLocal() as session:
        yield session

# --- Endpoints ---

@app.get("/users/")
def read_users(db: Session = Depends(get_db)):
    # .scalars() and .all() is the 2.0 way to handle results
    from sqlalchemy import select
    query = select(User)
    users = db.scalars(query).all()
    return users

    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)