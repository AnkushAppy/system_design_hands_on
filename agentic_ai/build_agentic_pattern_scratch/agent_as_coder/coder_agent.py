import sys
from io import StringIO

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


class CodingAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="cyankiwi/Qwen3.5-4B-AWQ-4bit", temperature=0, base_url="http://10.193.0.48:8000/v1")

    def execute_python(self, code: str):
        """Standard Python Sandbox (Simplified)"""
        print("[Sandbox] Executing generated tool...")
        old_stdout = sys.stdout
        redirected_output = sys.stdout = StringIO()
        try:
            # WARNING: Use a real sandbox (Docker/E2B) in production!
            exec(code)
            sys.stdout = old_stdout
            return redirected_output.getvalue()
        except Exception as e:
            sys.stdout = old_stdout
            return str(e)

    def solve(self, task: str):
        # 1. Ask LLM to write a tool
        prompt = f"""
        Write a Python script to solve the following: {task}
        Output ONLY the code. Do not explain. Ensure it prints the result.
        """
        code_str = self.llm.invoke([HumanMessage(content=prompt)]).content
        # Clean the code (remove ```python tags if present)
        code_str = code_str.replace("```python", "").replace("```", "")

        # 2. Execute the tool
        result = self.execute_python(code_str)
        return result

# Example: 
coder = CodingAgent(); 
print(coder.solve("Calculate the Creatinine Clearance using the Cockcroft-Gault formula for a 70kg, 65yo male with Creatinine 1.2."))