from typing import Self, ClassVar
from pydantic import BaseModel, ConfigDict, Field
import weakref

class Color(BaseModel):
    # 1. Make the model frozen (immutable) so it is hashable
    model_config = ConfigDict(frozen=True)

    r: int = Field(ge=0, le=255)
    g: int = Field(ge=0, le=255)
    b: int = Field(ge=0, le=255)

    # 2. The Interning Pool 
    # We use WeakValueDictionary so that if no one is using a color anymore, 
    # Python can garbage collect it.
    _pool: ClassVar[weakref.WeakValueDictionary] = weakref.WeakValueDictionary()

    @classmethod
    def get_color(cls, r: int, g: int, b: int) -> "Color":
        """The Interning Factory Method."""
        key = (r, g, b)
        
        # Check if we already have this color instance
        if key not in cls._pool:
            # Create, validate, and store a new instance
            instance = cls(r=r, g=g, b=b)
            cls._pool[key] = instance
            
        return cls._pool[key]

# --- Demonstration ---

def main():
    # Create "Red" twice
    color1 = Color.get_color(255, 0, 0)
    color2 = Color.get_color(255, 0, 0)

    # Create "Blue"
    color3 = Color.get_color(0, 0, 255)

    print(f"Color 1 ID: {id(color1)}")
    print(f"Color 2 ID: {id(color2)}")
    print(f"Color 3 ID: {id(color3)}")

    # Identity Check
    if color1 is color2:
        print("\n✅ Interning Success: color1 and color2 are the same object.")
    else:
        print("\n❌ Interning Failed: color1 and color2 are different objects.")

    if color1 is not color3:
        print("✅ Correct: color1 and color3 are different objects.")

    # Memory efficiency simulation
    many_reds = [Color.get_color(255, 0, 0) for _ in range(10000)]
    print(f"\nCreated 10,000 references to Red. Pool size: {len(Color._pool)}")

    # Pydantic validation still works
    try:
        Color.get_color(300, 0, 0) # Invalid RGB
    except ValueError as e:
        print(f"\n❌ Validation works: {e.errors()[0]['msg']}")

if __name__ == "__main__":
    main()