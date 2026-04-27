import os
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Utility function to get the LLM
def get_llm(model_name: str, temperature: float = 0, base_url: str = "http://10.193.0.48:8000/v1") -> ChatOpenAI:
    return ChatOpenAI(model=model_name, temperature=temperature, base_url=base_url)

class ClinicalReflectionAgent:
    def __init__(self, raw_patient_data: str, llm: ChatOpenAI = None, model_name: str = None, temperature: float = 0, base_url: str = "http://10.193.0.48:8000/v1"):
        self.raw_data = raw_patient_data
        if llm is None:
            model_name = model_name or os.getenv("MODEL_NAME", "cyankiwi/Qwen3.5-4B-AWQ-4bit")
            self.llm = get_llm(model_name=model_name, temperature=temperature, base_url=base_url)
        else:
            self.llm = llm
        self.history: List[Dict[str, str]] = []

    def _call_llm(self, prompt: str, system_message: str) -> str:
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=prompt)
        ]
        response = self.llm.invoke(messages)
        return response.content

    def generate_history(self) -> str:
        """Step 1: Draft the initial clinical history"""
        print("\n[Stage 1: Drafting Clinical History]")
        system_prompt = (
            "You are a meticulous Junior Doctor. Your task is to convert raw patient notes "
            "into a professional Clinical History. Use standard medical headings: "
            "Chief Complaint, History of Presenting Illness (HPI), Past Medical History (PMH), "
            "Medications, and Social History. Be concise and use medical terminology."
        )
        response = self._call_llm(self.raw_data, system_message=system_prompt)
        return response

    def reflect_and_critique(self, draft: str) -> str:
        """Step 2: Audit the history for medical completeness (Reflection)"""
        print("\n[Stage 2: Consultant Audit (Reflection)]")
        reflection_prompt = (
            f"Review the following clinical history draft for completeness and safety:\n\n{draft}\n\n"
            "Check for:\n"
            "1. Missing 'Red Flags' associated with the chief complaint.\n"
            "2. Lack of detail in the HPI (Onset, Location, Duration, Character, etc.).\n"
            "3. Ambiguity or non-professional language.\n"
            "4. Missing relevant negative findings."
        )
        system_prompt = (
            "You are a Senior Medical Consultant and Clinical Auditor. You are critical and "
            "focused on patient safety and diagnostic clarity. Identify what the Junior Doctor missed."
        )
        critique = self._call_llm(reflection_prompt, system_message=system_prompt)
        return critique

    def revise_history(self, draft: str, critique: str) -> str:
        """Step 3: Revise the history based on the audit"""
        print("\n[Stage 3: Final Clinical Revision]")
        revision_prompt = (
            f"Original Draft:\n{draft}\n\n"
            f"Consultant Critique:\n{critique}\n\n"
            "Rewrite the clinical history to be comprehensive, professional, and address all the consultant's concerns."
        )
        system_prompt = "You are an expert Physician. Finalize the medical documentation for the official patient record."
        final_output = self._call_llm(revision_prompt, system_message=system_prompt)
        return final_output

    def run(self, iterations: int = 1):
        """Orchestrates the Reflection Loop"""
        # 1. Initial Draft
        current_history = self.generate_history()
        print(f"--- Initial Draft ---\n{current_history}")

        # 2. Iterative Improvement
        for i in range(iterations):
            print(f"\n--- Iteration {i+1} ---")
            critique = self.reflect_and_critique(current_history)
            print(f"Critique:\n{critique}")
            
            current_history = self.revise_history(current_history, critique)
            print(f"Revised History:\n{current_history}")

        return current_history

# --- Main Execution ---
if __name__ == "__main__":
    # Example raw, messy patient notes
    patient_notes = """
    Patient is a 55 year old male, John Doe. Came in complaining of chest pain that started 2 hours ago 
    while shoveling snow. He says it feels like a heavy weight on his chest. It goes into his left jaw. 
    He's sweaty. He has high blood pressure and takes some blue pill for it. He smokes a pack a day. 
    No allergies he can remember.
    """
    
    agent = ClinicalReflectionAgent(patient_notes)
    # Running with 1 iteration of reflection
    final_report = agent.run(iterations=1)
    
    print("\n================ FINAL CLINICAL RECORD ================")
    print(final_report)