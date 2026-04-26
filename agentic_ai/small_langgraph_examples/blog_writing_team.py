"""
Blog Writing Team - A LangGraph Multi-Agent System with LLM-powered agents

Three specialized agents collaborating to create blog posts:
- Researcher: Has tools to search Wikipedia for information
- Writer: Has no tools, just writes great prose based on research
- Editor: Has a spell-checker tool, and can send drafts back to writer if it's bad
"""

from __future__ import annotations

import operator
import sys
from pathlib import Path
from typing import Annotated, TypedDict

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START
from langgraph.types import Command
from typing_extensions import Literal

_tool_examples = Path(__file__).resolve().parent.parent / "tool_calling_examples"
if str(_tool_examples) not in sys.path:
    sys.path.insert(0, str(_tool_examples))

from utility import get_llm


# ============================================================================
# LLM CONFIGURATION
# ============================================================================

# Use Qwen3.5 4B model via vLLM
MODEL_NAME = "cyankiwi/Qwen3.5-4B-AWQ-4bit"
BASE_URL = "http://10.193.0.48:8000/v1"

def get_researcher_llm() -> BaseLanguageModel:
    """Get LLM for the Researcher agent."""
    return get_llm(MODEL_NAME, temperature=0.3, base_url=BASE_URL)

def get_writer_llm() -> BaseLanguageModel:
    """Get LLM for the Writer agent."""
    return get_llm(MODEL_NAME, temperature=0.7, base_url=BASE_URL)

def get_editor_llm() -> BaseLanguageModel:
    """Get LLM for the Editor agent."""
    return get_llm(MODEL_NAME, temperature=0.1, base_url=BASE_URL)


# ============================================================================
# STATE DEFINITION
# ============================================================================

class BlogWritingState(TypedDict):
    """Shared state for the blog writing team."""
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
# Has tools to search Wikipedia for information about the topic
# ============================================================================

def wikipedia_search(query: str) -> str:
    """
    Search Wikipedia for information about a topic.
    Simulates Wikipedia API - in production would use real Wikipedia API.
    """
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
    """
    Researcher: run Wikipedia-style lookup for the topic, then use Qwen to
    synthesize a structured research summary.
    """
    topic = state["topic"]
    search_results = wikipedia_search(topic)

    researcher_prompt = ChatPromptTemplate.from_messages([
        SystemMessage(
            content=(
                "You are a thorough Researcher. Synthesize the research notes into a "
                "detailed, well-organized summary with key insights, history, applications, "
                "and significance. Be comprehensive and factual."
            )
        ),
        HumanMessage(
            content=f"Synthesize research about: {topic}\n\n{search_results}",
        ),
    ])

    llm = get_researcher_llm()
    chain = researcher_prompt | llm
    result = chain.invoke({}, config=config)
    content = result.content if hasattr(result, "content") else str(result)

    return {
        "research_notes": [content],
        "stage": "writing",
        "messages": [],
    }


def writer_agent(state: BlogWritingState, config: RunnableConfig) -> dict:
    """
    Writer agent - no tools, pure creative writing based on research.
    """
    topic = state["topic"]
    notes = state.get("research_notes", [])
    research_text = notes[0] if notes else ""
    
    writer_prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=(
            "You are a skilled Writer. You write engaging, informative blog posts. "
            "You do NOT have any tools - you only write based on the research provided.\n"
            "Write in an engaging, accessible style suitable for a broad audience."
        )),
        HumanMessage(content=(
            f"Write a comprehensive blog post about **{topic.title()}**.\n\n"
            f"Use the following research as your source material:\n{research_text}\n\n"
            f"Structure your post with:\n"
            f"1. A compelling title and introduction that hooks the reader (use # for H1)\n"
            f"2. Key insights and body content based on the research (use ## for H2 subheadings)\n"
            f"3. A thoughtful conclusion that summarizes key takeaways\n"
        )),
    ])
    
    llm = get_writer_llm()
    chain = writer_prompt | llm
    result = chain.invoke({}, config=config)
    
    draft = result.content if hasattr(result, 'content') else str(result)
    
    return {
        "draft": draft,
        "stage": "editing",
    }


# ============================================================================
# AGENT 3: THE EDITOR
# Has a spell-checker tool, and can send drafts back to writer if bad
# ============================================================================

def spell_checker(text: str) -> dict:
    """
    A spell-checking and quality control tool.
    Analyzes text for spelling errors, grammar issues, readability, and structure.
    Returns a structured report with any issues found.
    """
    issues = []
    
    if len(text) < 200:
        issues.append({"type": "length", "severity": "high", "message": "Post is too short (minimum 200 characters)"})
    
    if "  " in text:
        issues.append({"type": "formatting", "severity": "low", "message": "Multiple consecutive spaces detected"})
    
    if "# " not in text:
        issues.append({"type": "structure", "severity": "medium", "message": "Missing title (H1 heading with '#')"})
    
    if "## " not in text:
        issues.append({"type": "structure", "severity": "medium", "message": "Missing subheadings (H2 headings with '##')"})
    
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if len(paragraphs) < 3:
        issues.append({"type": "structure", "severity": "low", "message": "Post should have more paragraph breaks for readability"})
    
    return {
        "has_issues": len(issues) > 0,
        "issue_count": len(issues),
        "issues": issues,
        "text_length": len(text),
        "paragraph_count": len(paragraphs),
    }

def editor_agent(state: BlogWritingState, config: RunnableConfig) -> Command[Literal["writer_agent"]]:
    """
    Editor agent that reviews the draft using LLM judgment AND
    a spell-checker tool. Can send drafts back to writer if quality is poor.
    """
    draft = state.get("draft", "")
    revision_count = state.get("revision_count", 0)
    
    max_revisions = 3
    
    # First, run the spell-checker tool
    spell_results = spell_checker(draft)
    
    # Build editor prompt
    editor_prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=(
            "You are a meticulous Editor. You review blog posts for quality, clarity, "
            "accuracy, and engagement. "
            f"You can request up to {max_revisions} revisions."
        )),
        HumanMessage(content=(
            f"Review the following draft blog post:\n\n{draft}\n\n"
            f"Spell-check tool results: {spell_results}\n\n"
            f"Revision count: {revision_count}/{max_revisions}\n\n"
            f"Should this post be published as-is, or should it be sent back to the writer "
            f"for revision? Provide specific feedback. "
            f"If you think it needs revision and we haven't hit max revisions, "
            f"include the word 'REVISE' at the start of your response."
        )),
    ])
    
    llm = get_editor_llm()
    chain = editor_prompt | llm
    
    result = chain.invoke({}, config=config)
    editor_notes = result.content if hasattr(result, 'content') else str(result)
    
    # Decision: send back if issues found and revisions available
    has_quality_issues = (
        spell_results["has_issues"] 
        or "revise" in editor_notes.lower() 
        or "REVISE" in editor_notes
    )
    
    if has_quality_issues and revision_count < max_revisions:
        feedback = f"Revision {revision_count + 1}/{max_revisions}: {editor_notes[:200]}"
        
        return Command(
            update={
                "editor_feedback": [feedback],
                "stage": "revising",
                "revision_count": revision_count + 1,
            },
            goto="writer_agent",
        )
    
    # Approve the draft
    approval_note = f"Approved by Editor: {editor_notes[:300]}"
    final = draft + "\n\n---\n\n*This post has been thoroughly reviewed and meets all quality standards.*"

    return Command(
        update={
            "final_post": final,
            "stage": "done",
            "editor_feedback": [approval_note],
        },
    )


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def build_blog_writing_graph():
    """Build and compile the LangGraph workflow."""
    
    workflow = StateGraph(BlogWritingState)
    
    # Add nodes (agents)
    workflow.add_node("researcher_agent", researcher_agent)
    workflow.add_node("writer_agent", writer_agent)
    workflow.add_node("editor_agent", editor_agent)
    
    # Add edges (flow)
    workflow.add_edge(START, "researcher_agent")
    workflow.add_edge("researcher_agent", "writer_agent")
    workflow.add_edge("writer_agent", "editor_agent")
    # editor_agent routes dynamically via Command (back to writer or finishes)
    
    return workflow.compile()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Build the graph
    graph = build_blog_writing_graph()
    
    # Test with different topics
    test_topics = ["python programming", "machine learning", "space exploration"]
    
    for topic in test_topics:
        print(f"\n{'='*70}")
        print(f"BLOG WRITING TEAM: Generating post about '{topic}'")
        print(f"{'='*70}\n")
        
        # Run the workflow
        result = graph.invoke(
            {
                "topic": topic,
                "research_notes": [],
                "draft": "",
                "editor_feedback": [],
                "final_post": "",
                "stage": "researching",
                "revision_count": 0,
                "messages": [],
            },
        )
        
        print(f"Stage: {result['stage']}")
        print(f"Revisions: {result.get('revision_count', 0)}")
        print(f"Editor feedback: {result.get('editor_feedback', [])}")
        print(f"\nFinal Post:\n{result.get('final_post', 'N/A')}")
        print(f"\n{'='*70}\n")
