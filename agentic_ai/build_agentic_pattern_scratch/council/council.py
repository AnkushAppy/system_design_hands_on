from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

class MedicalCouncil:
    def __init__(self):
        self.llm = ChatOpenAI(model="cyankiwi/Qwen3.5-4B-AWQ-4bit", temperature=0.7, base_url="http://10.193.0.48:8000/v1")
        
    def run_council(self, patient_case: str):
        # 1. Define the Specialists
        specialists = {
            "Optimist": "You focus on the best-case scenario and look for signs of recovery/health.",
            "Skeptic": "You focus on 'Red Flags'. What are we missing? What could go wrong? Be critical.",
            "Fact-Checker": "You focus strictly on medical guidelines and clinical evidence. No intuition."
        }
        
        council_responses = {}

        # 2. Collect opinions
        for role, instructions in specialists.items():
            print(f"[Council] Consulting the {role}...")
            response = self.llm.invoke([
                SystemMessage(content=instructions),
                HumanMessage(content=f"Review this case: {patient_case}")
            ]).content
            council_responses[role] = response

        # 3. The Judge / Moderator
        print("[Council] Judge is weighing the evidence...")
        judge_prompt = f"""
        You are a Chief Medical Officer. Review these three specialist opinions and provide a final, safe consensus.
        
        Optimist View: {council_responses['Optimist']}
        Skeptic View: {council_responses['Skeptic']}
        Fact-Checker View: {council_responses['Fact-Checker']}
        """
        
        final_verdict = self.llm.invoke([
            SystemMessage(content="Consolidate the opinions into a final clinical plan."),
            HumanMessage(content=judge_prompt)
        ]).content
        
        return final_verdict

# Example Usage
council = MedicalCouncil()
print(council.run_council("45yo male, chest pain, normal EKG, but high cholesterol."))