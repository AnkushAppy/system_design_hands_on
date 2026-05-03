from typing import Protocol, runtime_checkable
from pydantic import BaseModel, Field

# --- 1. The Interface (Abstract Factory) ---
# We use a Protocol to define the "kit" of methods any Test Factory must provide.
@runtime_checkable
class TestFactory(Protocol):
    def get_num_questions(self) -> int: ...
    def make_question(self, pos: int) -> str: ...
    def make_responses(self, pos: int) -> list[str]: ...
    def get_value(self, pos: int) -> int: ...
    def get_correct_response_index(self, pos: int) -> int: ...


# --- 2. Concrete Factory Implementation ---
class MathTestFactory:
    def __init__(self):
        # Specific data for this factory
        self._data = [
            {
                "q": "What is 7 x 8?",
                "r": ["48", "56", "64"],
                "v": 10,
                "c": 1  # Index of "56"
            },
            {
                "q": "What is the square root of 81?",
                "r": ["7", "8", "9", "10"],
                "v": 5,
                "c": 2  # Index of "9"
            }
        ]

    def get_num_questions(self) -> int:
        return len(self._data)

    def make_question(self, pos: int) -> str:
        return self._data[pos]["q"]

    def make_responses(self, pos: int) -> list[str]:
        return self._data[pos]["r"]

    def get_value(self, pos: int) -> int:
        return self._data[pos]["v"]

    def get_correct_response_index(self, pos: int) -> int:
        return self._data[pos]["c"]


# --- 3. The Test Logic (The Client) ---
class Test:
    def __init__(self, factory: TestFactory):
        self._factory = factory
        self._total_score = 0
        self._max_possible_score = 0

    def run(self):
        """Main logic to iterate through questions and calculate score."""
        num_q = self._factory.get_num_questions()
        
        for i in range(num_q):
            print(f"\nQuestion {i+1}: {self._factory.make_question(i)}")
            responses = self._factory.make_responses(i)
            value = self._factory.get_value(i)
            correct_idx = self._factory.get_correct_response_index(i)
            
            self._max_possible_score += value
            
            # Show options
            for idx, resp in enumerate(responses):
                print(f"  {idx}) {resp}")
            
            # Simulate User Input (In a real app, this might be a UI or API)
            try:
                user_choice = int(input("Your answer (index): "))
                if user_choice == correct_idx:
                    print("Correct!")
                    self._total_score += value
                else:
                    print(f"Wrong. The answer was {responses[correct_idx]}")
            except (ValueError, IndexError):
                print("Invalid input - skipping question.")

    def get_total(self) -> int:
        return self._total_score

    def get_max(self) -> int:
        return self._max_possible_score


# --- 4. Test Driver ---
class TestDriver:
    @staticmethod
    def main():
        # The Test logic is totally independent of the Math content.
        # We could pass a HistoryTestFactory here without changing the Test class.
        math_factory = MathTestFactory()
        t = Test(math_factory)
        
        t.run()
        
        print("\n" + "="*20)
        print(f"YOUR SCORE = {t.get_total()}/{t.get_max()}")
        print("="*20)

if __name__ == "__main__":
    TestDriver.main()