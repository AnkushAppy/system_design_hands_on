from abc import ABC, abstractmethod
from pydantic import BaseModel, Field

# --- 1. The Products (Do not change these) ---
class Question(BaseModel):
    text: str = ""
    responses: list[str] = Field(default_factory=list)
    correct_response: str = ""

class Test(BaseModel):
    name: str = "Default Test"
    questions: list[Question] = Field(default_factory=list)


# --- 2. The Abstract Builder ---
class TestBuilder(ABC):
    def __init__(self):
        # As per instructions: protected Test test = new Test()
        self.test = Test()

    def get_test(self) -> Test:
        return self.test

    @abstractmethod
    def add_question(self, pos: int) -> None:
        pass

    @abstractmethod
    def add_responses(self, pos: int) -> None:
        pass

    @abstractmethod
    def add_correct_response(self, pos: int) -> None:
        pass


# --- 3. Concrete Builder ---
# This class knows the SPECIFIC data for a Math Test.
class MathTestBuilder(TestBuilder):
    def __init__(self):
        super().__init__()
        self.test.name = "Calculus Quiz"
        # Source data for the builder to pull from
        self._raw_data = [
            {
                "q": "What is the derivative of x^2?",
                "r": ["x", "2x", "x^3", "0"],
                "c": "2x"
            },
            {
                "q": "What is 5 + 5?",
                "r": ["5", "10", "15"],
                "c": "10"
            }
        ]

    def add_question(self, pos: int) -> None:
        # Ensure the question object exists in the list
        while len(self.test.questions) <= pos:
            self.test.questions.append(Question())
        
        self.test.questions[pos].text = self._raw_data[pos]["q"]

    def add_responses(self, pos: int) -> None:
        self.test.questions[pos].responses = self._raw_data[pos]["r"]

    def add_correct_response(self, pos: int) -> None:
        self.test.questions[pos].correct_response = self._raw_data[pos]["c"]


# --- 4. The Director (TestDriver) ---
# This class defines the ORDER of construction.
class TestDriver:
    def __init__(self, builder: TestBuilder):
        self._builder = builder

    def construct_test(self):
        """The algorithm for building a test"""
        # Build 2 questions step by step
        for i in range(2):
            self._builder.add_question(i)
            self._builder.add_responses(i)
            self._builder.add_correct_response(i)
            
    def get_result(self) -> Test:
        return self._builder.get_test()


# --- Execution ---
if __name__ == "__main__":
    # 1. Pick a concrete builder
    math_builder = MathTestBuilder()

    # 2. Give the builder to the Director
    driver = TestDriver(math_builder)

    # 3. Director manages the construction process
    driver.construct_test()

    # 4. Get the final product
    final_test = driver.get_result()

    # Display results
    print(f"Test Name: {final_test.name}")
    for i, q in enumerate(final_test.questions):
        print(f"Q{i+1}: {q.text}")
        print(f"  Options: {q.responses}")
        print(f"  Answer: {q.correct_response}")