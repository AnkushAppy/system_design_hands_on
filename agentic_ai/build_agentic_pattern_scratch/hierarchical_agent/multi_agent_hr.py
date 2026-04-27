from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

class HospitalManager:
    def __init__(self):
        self.llm = ChatOpenAI(model="cyankiwi/Qwen3.5-4B-AWQ-4bit", temperature=0, base_url="http://10.193.0.48:8000/v1")
        
    def specialist_cardiology(self, query: str):
        return "Cardio-Worker: Analysis of EKG shows Sinus Tachycardia."

    def specialist_pharmacy(self, query: str):
        return "Pharmacy-Worker: Suggesting Beta-blockers, check for asthma contraindication."

    def run(self, user_request: str):
        # 1. The Manager decides who to call
        print("[Manager] Delegating tasks...")
        
        # In a real system, the LLM would output JSON to route these.
        # Here we simulate the Manager calling multiple sub-agents.
        cardio_info = self.specialist_cardiology(user_request)
        pharm_info = self.specialist_pharmacy(user_request)
        
        # 2. The Manager synthesizes the results
        print("[Manager] Synthesizing final report...")
        final_prompt = f"""
        You are the Hospital Director. Based on the reports from your specialists:
        Report 1: {cardio_info}
        Report 2: {pharm_info}
        
        Write the final discharge summary for the patient.
        """
        
        summary = self.llm.invoke([HumanMessage(content=final_prompt)]).content
        return summary

# Example: 
manager = HospitalManager(); print(manager.run("Patient with fast heart rate."))