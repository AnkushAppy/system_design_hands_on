import os
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# utility function to get the llm
def get_llm(model_name: str, temperature: float = 0, base_url: str = "http://10.193.0.48:8000/v1") -> ChatOpenAI:
    return ChatOpenAI(model=model_name, temperature=temperature, base_url=base_url)

class ReflectionAgent:
    def __init__(self, task: str, llm: ChatOpenAI = None, model_name: str = None, temperature: float = 0, base_url: str = "http://10.193.0.48:8000/v1"):
        self.task = task
        if llm is None:
            # Use model_name from parameter, environment variable, or default
            model_name = model_name or os.getenv("MODEL_NAME", "cyankiwi/Qwen3.5-4B-AWQ-4bit")
            self.llm = get_llm(model_name=model_name, temperature=temperature, base_url=base_url)
        else:
            self.llm = llm
        self.history: List[Dict[str, str]] = []

    def _call_llm(self, prompt: str, system_message: str = "You are a helpful assistant.") -> str:
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=prompt)
        ]
        response = self.llm.invoke(messages)
        return response.content

    def generate(self) -> str:
        """Step 1: Initial Draft Generation"""
        print("\n[Stage 1: Generation]")
        system_prompt = "You are an expert programmer. Write code to solve the user task."
        response = self._call_llm(self.task, system_message=system_prompt)
        self.history.append({"role": "assistant", "content": response})
        return response

    def reflect(self, draft: str) -> str:
        """Step 2: Self-Critique / Reflection"""
        print("\n[Stage 2: Reflection]")
        reflection_prompt = f"Critique the following code for bugs, efficiency, and readability. Be harsh:\n\n{draft}"
        system_prompt = "You are a senior code reviewer. Find flaws and suggest improvements."
        critique = self._call_llm(reflection_prompt, system_message=system_prompt)
        return critique

    def revise(self, draft: str, critique: str) -> str:
        """Step 3: Revision based on critique"""
        print("\n[Stage 3: Revision]")
        revision_prompt = f"Original Code: {draft}\n\nCritique: {critique}\n\nRewrite the code addressing all issues."
        system_prompt = "You are an expert programmer. Improve the code based on the provided critique."
        final_output = self._call_llm(revision_prompt, system_message=system_prompt)
        return final_output

    def run(self, iterations: int = 1):
        """Orchestrates the Reflection Loop"""
        # 1. Initial Attempt
        current_output = self.generate()
        print(f"Initial Draft:\n{current_output}")

        # 2. Iterative Reflection Loop
        for i in range(iterations):
            print(f"\n--- Iteration {i+1} ---")
            critique = self.reflect(current_output)
            print(f"Critique: {critique}")
            
            current_output = self.revise(current_output, critique)
            print(f"Revised Output:\n{current_output}")

        return current_output

# --- Main Execution ---
if __name__ == "__main__":
    task_description = "Write a Python function to double numbers in a list."
    
    agent = ReflectionAgent(task_description)
    final_result = agent.run(iterations=1)
    
    print("\n================ FINAL AGENT OUTPUT ================")
    print(final_result)