import os
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

class ClinicalMemoryAgent:
    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        self.llm = ChatOpenAI(
            model="cyankiwi/Qwen3.5-4B-AWQ-4bit", 
            temperature=0, 
            base_url="http://10.193.0.48:8000/v1"
        )
        # 1. Short-term Memory (List of messages in current session)
        self.short_term_history = []
        
        # 2. Mock Long-term Memory (In a real app, this would be a Vector Database like Pinecone/Chroma)
        self.long_term_memory = {
            "p_001": [
                "Patient has a known allergy to Penicillin (noted Jan 2023).",
                "Patient was diagnosed with Type 2 Diabetes in 2015.",
                "Patient prefers communication via email."
            ]
        }

    def _get_relevant_long_term_memory(self, query: str) -> str:
        """Simulates RAG (Retrieval Augmented Generation)"""
        # In a real system, we'd do a vector search here.
        facts = self.long_term_memory.get(self.patient_id, [])
        return "\n".join([f"- {f}" for f in facts])

    def chat(self, user_input: str):
        # Step A: Retrieve Long-term context
        relevant_facts = self._get_relevant_long_term_memory(user_input)
        
        # Step B: Build the System Message with 'Persona' and 'Knowledge'
        system_prompt = f"""
You are the dedicated Primary Care Physician for patient {self.patient_id}.
    
LONG-TERM PATIENT FACTS:
{relevant_facts}

INSTRUCTIONS:
- Use the patient facts to ensure safety (check for allergies).
- Maintain a consistent, caring persona.
- Refer to past history if relevant.
"""
        # Step C: Prepare messages (History + Current Input)
        messages = [SystemMessage(content=system_prompt)]
        messages.extend(self.short_term_history)
        messages.append(HumanMessage(content=user_input))

        # Step D: Get response
        response = self.llm.invoke(messages).content
        
        # Step E: Update Short-term memory
        self.short_term_history.append(HumanMessage(content=user_input))
        self.short_term_history.append(AIMessage(content=response))
        
        # Keep short-term memory lean (last 5 exchanges)
        if len(self.short_term_history) > 10:
            self.short_term_history = self.short_term_history[-10:]
            
        return response

# --- Execution ---
if __name__ == "__main__":
    agent = ClinicalMemoryAgent(patient_id="p_001")
    
    print("--- First Interaction ---")
    print("User: I have a sore throat. Can you prescribe Amoxicillin?")
    print(f"Agent: {agent.chat('I have a sore throat. Can you prescribe Amoxicillin?')}")
    
    print("\n--- Second Interaction (Short-term memory test) ---")
    print("User: Actually, what was that second fact you mentioned earlier?")
    print(f"Agent: {agent.chat('Actually, what was that second fact you mentioned earlier?')}")