import os
import json
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# 1. --- Setup LLM ---
def get_llm(model_name: str = "cyankiwi/Qwen3.5-4B-AWQ-4bit"):
    return ChatOpenAI(
        model=model_name, 
        temperature=0, 
        base_url="http://10.193.0.48:8000/v1"
    )

class PlanningAgent:
    def __init__(self, goal: str):
        self.goal = goal
        self.llm = get_llm()
        self.plan: List[str] = []
        self.results: List[str] = [] # Stores results of completed tasks

    def create_plan(self) -> List[str]:
        """Step 1: The Planner - Breaks the goal into sub-tasks"""
        print(f"\n[Planning Phase] Goal: {self.goal}")
        
        system_prompt = (
            "You are a Clinical Research Planner. Break the user's request into a "
            "numbered list of 3-4 logical, sequential sub-tasks. "
            "Output ONLY the numbered list."
        )
        
        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Goal: {self.goal}")
        ]).content
        
        # Simple parsing of numbered list into a Python list
        self.plan = [line.strip() for line in response.split('\n') if line.strip() and any(char.isdigit() for char in line[:2])]
        return self.plan

    def execute_task(self, task: str, context: str) -> str:
        """Step 2: The Executor - Completes a single sub-task"""
        print(f"\n[Executing Task]: {task}")
        
        system_prompt = (
            "You are a Medical Expert. Complete the assigned task based on the "
            "provided previous context. Be detailed and clinical."
        )
        
        prompt = f"Previous Context: {context}\n\nCurrent Task: {task}"
        
        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]).content
        return response

    def replan(self, failed_task: str, error_reason: str) -> List[str]:
        """Step 3: The Re-planner - Adjusts the plan if something goes wrong"""
        print(f"\n[Re-planning] Task failed: {failed_task}")
        
        system_prompt = (
            "You are a Clinical Project Manager. A sub-task has failed or provided "
            "unexpected results. Based on the error, revise the remaining plan."
        )
        
        prompt = (
            f"Original Goal: {self.goal}\n"
            f"Completed Tasks: {self.results}\n"
            f"Failed Task: {failed_task}\n"
            f"Reason: {error_reason}\n"
            f"Current Plan: {self.plan}\n"
            "Provide a new list of remaining tasks."
        )
        
        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]).content
        
        self.plan = [line.strip() for line in response.split('\n') if line.strip()]
        return self.plan

    def run(self):
        # 1. Create Initial Plan
        self.create_plan()
        print(f"Initial Plan: {self.plan}")

        step = 0
        while step < len(self.plan):
            current_task = self.plan[step]
            
            # Use all previous results as context
            context = "\n".join(self.results)
            
            # 2. Execute Task
            result = self.execute_task(current_task, context)
            
            # --- Simulation of a Re-planning trigger ---
            # If the task mentions "insufficient data", we trigger a re-plan
            if "insufficient data" in result.lower() and step == 1:
                print("!! Triggering Re-plan due to lack of specific data !!")
                self.replan(current_task, "Initial diagnostic criteria were too broad.")
                step = 0 # Restart or adjust logic based on new plan
                continue
            
            self.results.append(f"Task: {current_task}\nResult: {result}")
            step += 1

        return self.results

# --- Main Execution ---
if __name__ == "__main__":
    complex_goal = (
        "Create a comprehensive clinical management plan for a 65-year-old male "
        "with Type 2 Diabetes, Stage 3 Chronic Kidney Disease, and New-onset Atrial Fibrillation."
    )
    
    agent = PlanningAgent(complex_goal)
    final_output = agent.run()
    
    print("\n" + "="*50)
    print("FINAL CONSOLIDATED REPORT")
    print("="*50)
    for entry in final_output:
        print(f"\n{entry}")