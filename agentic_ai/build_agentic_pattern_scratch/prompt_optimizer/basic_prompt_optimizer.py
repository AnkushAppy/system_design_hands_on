import os
from typing import List, Dict

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

class PromptOptimizer:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="cyankiwi/Qwen3.5-4B-AWQ-4bit", 
            temperature=0.5, # Higher temp for variation
            base_url="http://10.193.0.48:8000/v1"
        )
        # Use a "Stronger" persona for the Judge
        self.judge_llm = self.llm 

    def run_test(self, patient_data: str):
        # 1. Define Candidate Prompts (Different strategies)
        candidates = [
            "Summarize this patient case concisely for a busy doctor.",
            "Explain this patient case using the SOAP (Subjective, Objective, Assessment, Plan) format.",
            "Describe this patient case in simple terms so a student can understand it."
        ]
        
        results = []

        # 2. Generation Phase: Try each prompt
        for i, prompt_variation in enumerate(candidates):
            print(f"[Testing Candidate {i+1}]...")
            response = self.llm.invoke([
                SystemMessage(content=prompt_variation),
                HumanMessage(content=patient_data)
            ]).content
            results.append({"prompt": prompt_variation, "response": response})

        # 3. Evaluation Phase: The 'Judge' scores the results
        print("\n[Judge Phase] Evaluating the best response...")
        best_response = self.evaluate(results, patient_data)
        return best_response

    def evaluate(self, results: List[Dict], original_data: str) -> Dict:
        eval_input = "Identify which of the following responses is the most CLINICALLY ACCURATE and PROFESSIONAL.\n\n"
        for i, res in enumerate(results):
            eval_input += f"--- OPTION {i} ---\n{res['response']}\n\n"

        system_message = (
            "You are a Senior Medical Auditor. Your job is to pick the best summary "
            "based on medical rigor and clarity. Output ONLY the index number (0, 1, or 2) "
            "of the best response."
        )

        choice = self.judge_llm.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=eval_input)
        ]).content

        # Extract index and return
        try:
            index = int(''.join(filter(str.isdigit, choice)))
            return results[index]
        except:
            return results[0] # Default to first if judge fails

# --- Execution ---
if __name__ == "__main__":
    patient_info = """
    Male, 45. History of asthma. Presents with shortness of breath. 
    O2 saturation 92%. Lung sounds: wheezing in all fields. 
    Prescribed Albuterol nebulizer.
    """
    
    optimizer = PromptOptimizer()
    best = optimizer.run_test(patient_info)
    
    print("\n" + "="*50)
    print(f"WINNING STRATEGY: {best['prompt']}")
    print("-" * 50)
    print(f"FINAL OUTPUT:\n{best['response']}")