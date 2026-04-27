import os
from typing import Tuple
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# 1. --- Define our Models ---
# In a real scenario, 'Small' might be Qwen-4B or GPT-4o-mini
# 'Large' might be GPT-4o, Claude 3.5, or Qwen-72B
SMALL_MODEL = "cyankiwi/Qwen3.5-4B-AWQ-4bit" # Fast & Cheap
LARGE_MODEL = "gpt-4.1-mini" # Smart & Expensive (Placeholder name)

def get_llm(model_name: str, base_url: str = "http://10.193.0.48:8000/v1"):
    return ChatOpenAI(
        model=model_name, 
        temperature=0, 
        base_url=base_url
    )

class RoutingDispatcher:
    def __init__(self):
        self.small_llm = get_llm(SMALL_MODEL)
        # For demonstration, we'll use the same endpoint, but in reality, this would be a larger model
        self.large_llm = get_llm(SMALL_MODEL) 

    def classify_request(self, query: str) -> str:
        """The Dispatcher: Decides if the query is SIMPLE or COMPLEX."""
        print(f"\n[Dispatcher] Analyzing query complexity...")
        
        system_prompt = (
            "You are a medical triage dispatcher. Classify the user's request.\n"
            "Classification Criteria:\n"
            "- SIMPLE: Basic medical definitions, general health facts, or greetings.\n"
            "- COMPLEX: Case studies, drug-drug interactions, diagnostic reasoning, or multi-step treatment plans.\n\n"
            "Respond with ONLY the word 'SIMPLE' or 'COMPLEX'."
        )
        
        response = self.small_llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]).content
        
        return "COMPLEX" if "COMPLEX" in response.upper() else "SIMPLE"

    def handle_request(self, query: str):
        # Step 1: Route the request
        route = self.classify_request(query)
        
        if route == "SIMPLE":
            print(f"--- Routing to SMALL MODEL ({SMALL_MODEL}) ---")
            system_message = "You are a helpful medical assistant. Give a brief, accurate answer."
            response = self.small_llm.invoke([
                SystemMessage(content=system_message),
                HumanMessage(content=query)
            ])
        else:
            print(f"--- Routing to LARGE MODEL ({LARGE_MODEL}) ---")
            system_message = (
                "You are a Senior Medical Consultant. Provide a deep, "
                "evidence-based analysis with clinical reasoning."
            )
            response = self.large_llm.invoke([
                SystemMessage(content=system_message),
                HumanMessage(content=query)
            ])
            
        return response.content, route

# --- Main Execution ---
if __name__ == "__main__":
    dispatcher = RoutingDispatcher()

    # Test Case 1: Simple Question
    q1 = "What is the normal resting heart rate for an adult?"
    answer1, used_route1 = dispatcher.handle_request(q1)
    print(f"Route: {used_route1}\nAnswer: {answer1}")

    print("\n" + "="*40)

    # Test Case 2: Complex Question
    q2 = (
        "A 72-year-old female with a history of AFib on Warfarin presents with "
        "a sudden onset of severe abdominal pain and bloody stools. What is the "
        "differential diagnosis and immediate management plan?"
    )
    answer2, used_route2 = dispatcher.handle_request(q2)
    print(f"Route: {used_route2}\nAnswer: {answer2}")