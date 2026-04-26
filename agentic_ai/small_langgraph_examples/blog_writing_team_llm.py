"""
Blog Writing Team - LangGraph Multi-Agent System with Qwen3.5 LLM

Three specialized agents collaborating to create blog posts:
- Researcher: Has Wikipedia search tool
- Writer: No tools, pure creative writing  
- Editor: Has spell-checker tool, can send drafts back for revision
"""

from __future__ import annotations
from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, START
from langgraph.types import Command
from typing_extensions import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.language_models import BaseLanguageModel

import sys
sys.path.insert(0, "/Users/ankush/system_design_hands_on/agentic_ai/tool_calling_examples")
from utility import get_llm


# ============================================================================
# LLM CONFIGURATION
# ============================================================================

MODEL_NAME = "cyankiwi/Qwen3.5-4B-AWQ-4bit"
BASE_URL = "http://10.193.0.48:8000/v1"

def get_researcher_llm() -> BaseLanguageModel:
    return get_llm(MODEL_NAME, temperature=0.3, base_url=BASE_URL)

def get_writer_llm() -> BaseLanguageModel:
    return get_llm(MODEL_NAME, temperature=0.7, base_url=BASE_URL)

def get_editor_llm() -> BaseLanguageModel:
    return get_llm(MODEL_NAME, temperature=0.1, base_url=BASE_URL)


# ============================================================================
# STATE DEFINITION
# ============================================================================

class BlogWritingState(TypedDict):
    topic: str
    research_notes: Annotated[list, operator.add]
    draft: str
    editor_feedback: Annotated[list, operator.add]
    final_post: str
    stage: str
    revision_count: int
    messages: Annotated[list, operator.add]


# ============================================================================
# AGENT 1: THE RESEARCHER
# Has Wikipedia search tool + LLM
# ============================================================================

def wikipedia_search(query: str) -> str:
    """Search Wikipedia for information about a topic."""
    wiki_database = {
        "python programming": [
            "Python is a high-level, interpreted programming language created by Guido van Rossum and first released in 1991.",
            "Python emphasizes code readability with significant indentation.",
            "Python supports multiple programming paradigms: procedural, object-oriented, and functional.",
            "Python has a large standard library and a vast ecosystem of third-party packages.",
            "Python's philosophy emphasizes simplicity and explicitness with the Zen of Python.",
            "Python is widely used in data science, machine learning, web development, and automation.",
            "Major frameworks include Django (full-stack) and Flask (micro-framework) for web development.",
            "Popular libraries for data science include NumPy, pandas, scikit-learn, and TensorFlow.",
            "Python 3.12 (released 2023) introduced performance improvements and new typing features.",
        ],
        "machine learning": [
            "Machine learning is a subset of artificial intelligence that enables systems to learn from data.",
            "Arthur Samuel coined the term 'machine learning' in 1959.",
            "There are three main types: supervised, unsupervised, and reinforcement learning.",
            "Supervised learning uses labeled datasets to train models for classification and regression.",
            "Linear regression, decision trees, and random forests are fundamental ML algorithms.",
            "Neural networks are inspired by the human brain's structure and function.",
            "Deep learning uses multi-layered neural networks for complex pattern recognition.",
            "Convolutional Neural Networks (CNNs) excel at image recognition tasks.",
            "Transformers and attention mechanisms revolutionized NLP, powering models like GPT.",
            "Scikit-learn provides simple and efficient tools for predictive data analysis.",
            "Python is the dominant language for ML, with libraries like TensorFlow, PyTorch, and Keras.",
            "Overfitting occurs when models memorize training data rather than generalizing patterns.",
        ],
        "space exploration": [
            "The Space Age began with the launch of Sputnik 1 by the Soviet Union on October 4, 1957.",
            "NASA's Apollo 11 mission landed the first humans on the Moon on July 20, 1969.",
            "The International Space Station (ISS) has been continuously occupied since November 2000.",
            "SpaceX's Falcon 9 was the first orbital rocket to achieve propulsive landing and reusability.",
            "The James Webb Space Telescope (JWST) launched in 2021 explores the early universe in infrared.",
            "Mars rovers Curiosity (2012) and Perseverance (2021) search for signs of ancient life.",
            "The Artemis program aims to return humans to the Moon and establish a sustainable presence.",
            "Voyager 1 and 2, launched in 1977, are the farthest human-made objects from Earth.",
            "The Hubble Space Telescope, launched in 1990, revolutionized our understanding of cosmology.",
            "Blue Origin and Virgin Galactic are pioneering commercial suborbital space tourism.",
            "The Event Horizon Telescope captured the first image of a black hole in 2019.",
        ],
    }
    results = wiki_database.get(query.lower(), [
        f"Information about {query} gathered from Wikipedia.",
        f"Key facts about {query} include its history, applications, and significance.",
        f"Recent developments in {query} show growing interest and innovation.",
    ])
    return "\n".join([f"- {r}" for r in results])


def researcher_agent(state: BlogWritingState, config: RunnableConfig) -> dict:
    topic = state["topic"]
    
    # Use Wikipedia search tool
    search_results = wikipedia_search(topic)
    
    # LLM synthesizes the research
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=(
            "You are a thorough Researcher. Synthesize the Wikipedia research into a "
            "detailed, well-organized summary. Be concise - max 200 words."
        )),
        HumanMessage(content=f"Synthesize research about: {topic}\n\n{search_results}"),
    ])
    
    print("  [Researcher] Invoking LLM...")
    llm = get_researcher_llm()
    chain = prompt | llm
    result = chain.invoke({}, config=config)
    content = result.content if hasattr(result, "content") else str(result)
    print(f"  [Researcher] Got {len(content)} chars")
    
    return {
        "research_notes": [content],
        "stage": "writing",
        "messages": [],
    }


# ============================================================================
# AGENT 2: THE WRITER
# No tools - pure creative writing
# ============================================================================

def writer_agent(state: BlogWritingState) -> dict:
    topic = state["topic"]
    notes = state.get("research_notes", [])
    research_text = notes[0] if notes else ""
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=(
            "You are a skilled Writer. Write engaging, informative blog posts.\n"
            "You have NO tools. Be concise - write about 3-4 short paragraphs.\n"
            "Use # for H1 title, ## for H2 subheadings."
        )),
        HumanMessage(content=(
            f"Write a blog post about **{topic.title()}**.\n\n"
            f"Source: {research_text[:500]}\n\n"
            f"Include: title, intro, key insights (2-3), conclusion.\n"
        )),
    ])
    
    llm = get_writer_llm()
    chain = prompt | llm
    print("  [Writer] Invoking LLM...")
    result = chain.invoke({})
    draft = result.content if hasattr(result, "content") else str(result)
    print(f"  [Writer] Got {len(draft)} chars")
    
    return {
        "draft": draft,
        "stage": "editing",
    }


# ============================================================================
# AGENT 3: THE EDITOR
# Has spell-checker tool, can send drafts back to writer
# ============================================================================

def spell_checker(text: str) -> dict:
    """Analyze text for quality issues."""
    issues = []
    if len(text) < 200:
        issues.append({"type": "length", "severity": "high", "message": "Post too short (min 200 chars)"})
    if "  " in text:
        issues.append({"type": "formatting", "severity": "low", "message": "Multiple consecutive spaces"})
    if "# " not in text:
        issues.append({"type": "structure", "severity": "medium", "message": "Missing title (H1 with #)"})
    if "## " not in text:
        issues.append({"type": "structure", "severity": "medium", "message": "Missing subheadings (H2 with ##)"})
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) < 3:
        issues.append({"type": "structure", "severity": "low", "message": "Add more paragraph breaks"})
    return {
        "has_issues": len(issues) > 0,
        "issue_count": len(issues),
        "issues": issues,
        "text_length": len(text),
        "paragraph_count": len(paragraphs),
    }


def editor_agent(state: BlogWritingState, config: RunnableConfig) -> Command[Literal["writer_agent"]]:
    draft = state.get("draft", "")
    revision_count = state.get("revision_count", 0)
    max_revisions = 3
    
    # Run spell-checker tool
    spell_results = spell_checker(draft)
    
    # LLM reviews the draft
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=(
            "You are a meticulous Editor. Review blog posts for quality, clarity, "
            f"accuracy, and engagement. You can request up to {max_revisions} revisions."
        )),
        HumanMessage(content=(
            f"Review this draft:\n\n{draft}\n\n"
            f"Spell-check results: {spell_results}\n\n"
            f"Revision: {revision_count}/{max_revisions}\n\n"
            f"If it needs revision and we haven't hit max revisions, start your response with 'REVISE'. "
            f"Provide specific feedback and decide: publish or revise?"
        )),
    ])
    
    llm = get_editor_llm()
    chain = prompt | llm
    result = chain.invoke({}, config=config)
    editor_notes = result.content if hasattr(result, "content") else str(result)
    print(f"  [Editor] Got {len(editor_notes)} chars")
    
    # Decide whether to send back for revision
    needs_revision = (
        spell_results["has_issues"]
        or "revise" in editor_notes.lower()
        or "REVISE" in editor_notes
    )
    
    if needs_revision and revision_count < max_revisions:
        feedback = f"Revision {revision_count + 1}/{max_revisions}: {editor_notes[:200]}"
        return Command(
            update={
                "editor_feedback": [feedback],
                "stage": "revising",
                "revision_count": revision_count + 1,
            },
            goto="writer_agent",
        )
    
    # Approve
    approval = f"Editor approved: {editor_notes[:300]}"
    final = draft + "\n\n---\n\n*This post has been thoroughly reviewed and meets all quality standards.*"
    return Command(
        update={
            "final_post": final,
            "stage": "done",
            "editor_feedback": [approval],
        },
    )


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def build_blog_writing_graph():
    workflow = StateGraph(BlogWritingState)
    workflow.add_node("researcher_agent", researcher_agent)
    workflow.add_node("writer_agent", writer_agent)
    workflow.add_node("editor_agent", editor_agent)
    workflow.add_edge(START, "researcher_agent")
    workflow.add_edge("researcher_agent", "writer_agent")
    workflow.add_edge("writer_agent", "editor_agent")
    # editor routes back to writer via Command, or finishes
    return workflow.compile()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    graph = build_blog_writing_graph()
    
    test_topics = ["python programming", "machine learning", "space exploration"]
    
    for topic in test_topics:
        print(f"\n{'='*70}")
        print(f"BLOG WRITING TEAM: Generating post about '{topic}'")
        print(f"{'='*70}\n")
        
        result = graph.invoke({
            "topic": topic,
            "research_notes": [],
            "draft": "",
            "editor_feedback": [],
            "final_post": "",
            "stage": "researching",
            "revision_count": 0,
            "messages": [],
        })
        
        print(f"Stage: {result['stage']}")
        print(f"Revisions: {result.get('revision_count', 0)}")
        print(f"Editor feedback: {result.get('editor_feedback', [])}")
        print(f"\nFinal Post:\n{result.get('final_post', 'N/A')}\n")
        print(f"{'='*70}\n")
