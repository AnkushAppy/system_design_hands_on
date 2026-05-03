from typing import Any
from threading import Lock
from pydantic import BaseModel, Field

# 1. Inherit from the same type as BaseModel's metaclass
class SingletonMeta(type(BaseModel)):
    _instances: dict[type, Any] = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

# 2. Now this works without conflict
class DatabaseConfig(BaseModel, metaclass=SingletonMeta):
    connection_string: str = "postgresql://localhost:5432/db"
    timeout: int = 30

    # Pydantic V2 specific: ensure the model doesn't try to re-init 
    # if you call DatabaseConfig() a second time with different args.
    def __init__(self, **data):
        # Only initialize if the object is brand new
        if not hasattr(self, "__pydantic_fields_set__") or not self.__pydantic_fields_set__:
            super().__init__(**data)

# 3. Test it
if __name__ == "__main__":
    db1 = DatabaseConfig(timeout=60)
    db2 = DatabaseConfig(timeout=999)

    print(f"ID db1: {id(db1)}")
    print(f"ID db2: {id(db2)}")
    print(f"Timeout: {db2.timeout}")  # Remains 60 because db1 was first
    print(f"Are they the same? {db1 is db2}")