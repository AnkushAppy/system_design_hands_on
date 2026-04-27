import os
import re
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# 1. --- Define Our Tools (The "Actions") ---
def get_drug_dosage(drug_name: str) -> str:
    """Simulates a lookup in a medical database."""
    db = {
        "amoxicillin": "Adults: 500mg every 8 hours. Pediatrics: 20-40mg/kg/day.",
        "ibuprofen": "Adults: 400mg every 4-6 hours. Max 3200mg/day.",
        "lisinopril": "Adults: 10mg once daily starting dose."
    }
    return db.get(drug_name.lower(), "Drug not found in database.")

def check_patient_allergies(patient_name: str) -> str:
    """Simulates a lookup in an Electronic Health Record (EHR)."""
    records = {
        "john doe": "Penicillin, Sulfa drugs",
        "jane smith": "No known allergies (NKDA)"
    }
    return records.get(patient_name.lower(), "Patient record not found.")

# Mapping strings to actual functions
TOOLS = {
    "get_drug_dosage": get_drug_dosage,
    "check_patient_allergies": check_patient_allergies
}

# 2. --- The ReAct Agent ---
class ReActAgent:
    def __init__(self, model_name: str = "cyankiwi/Qwen3.5-4B-AWQ-4bit", base_url: str = "http://10.193.0.48:8000/v1"):
        self.llm = ChatOpenAI(
            model=model_name, 
            temperature=0, 
            base_url=base_url
        )
        self.system_prompt = """
You are a Clinical Assistant. You have access to the following tools:

- get_drug_dosage(drug_name): Returns the standard dosage for a drug.
- check_patient_allergies(patient_name): Returns a list of patient allergies.

To use a tool, you MUST use the following format:
Thought: [Your reasoning about what to do]
Action: [tool_name]
Action Input: [input for the tool]

Once you have an Observation from the tool, you will repeat the process until you have the final answer.
When you have the final answer, use this format:
Thought: I have all the information needed.
Final Answer: [Your complete response to the user]
"""

    def run(self, user_question: str, max_steps: int = 5):
        print(f"User Question: {user_question}")
        
        # We maintain the conversation as a growing string
        trajectory = f"\nUser: {user_question}"
        
        for i in range(max_steps):
            # Step A: Ask the LLM for a Thought and Action
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=trajectory)
            ]
            response = self.llm.invoke(messages).content
            print(f"\n--- Step {i+1} ---")
            print(response)

            # Check if the LLM provided a Final Answer
            if "Final Answer:" in response:
                return response.split("Final Answer:")[-1].strip()

            # Step B: Parse the Action and Action Input
            try:
                action = re.search(r"Action: (.*)", response).group(1).strip()
                action_input = re.search(r"Action Input: (.*)", response).group(1).strip()
                
                # Step C: Execute the Tool
                if action in TOOLS:
                    print(f"[Executing {action} with input: {action_input}]")
                    observation = TOOLS[action](action_input)
                else:
                    observation = f"Error: Tool {action} does not exist."
                
                print(f"Observation: {observation}")
                
                # Step D: Update the trajectory with the result
                trajectory += f"\n{response}\nObservation: {observation}"
                
            except Exception as e:
                return f"Failed to parse agent response: {str(e)}"

        return "Agent reached maximum steps without a final answer."

# 3. --- Main Execution ---
if __name__ == "__main__":
    agent = ReActAgent()
    
    # Complex query requiring two tool calls
    question = "Can I give Amoxicillin to John Doe? If so, what is the dose?"
    
    result = agent.run(question)
    
    print("\n================ FINAL AGENT OUTPUT ================")
    print(result)