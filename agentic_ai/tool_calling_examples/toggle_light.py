"""
Home Automation Agent

This module demonstrates a LangChain-based home automation agent that can control
various smart devices through tool calling. The agent is configured with multiple
tools for interacting with lights, thermostat, door locks, and security systems.

Tools:
    - toggle_light: Control lights in a room
    - lock_door: Lock a specified door
    - unlock_door: Unlock a specified door
    - adjust_thermostat: Set temperature for a specific zone
    - check_security_system: Check the status of the security system

Usage:
    Run the script directly to execute the default user queries, or modify the
    user_queries list to test different scenarios.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from enum import StrEnum
from typing import Any

import pytz

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain.tools import tool
from langchain_core.callbacks import UsageMetadataCallbackHandler

from langgraph.checkpoint.memory import InMemorySaver

from utility import LlmCallMetricsHandler, get_llm


class Home:
    """
    Persistent home state manager.
    
    Manages rooms, doors, thermostats, security system, and action logs.
    State is persisted to a JSON file for continuity across runs.
    """
    
    def __init__(self, data_file: str | None = None):
        if data_file is None:
            # Use absolute path in same directory as this script
            data_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "home_state.json"
            )
        self.data_file = data_file
        self.rooms: dict[str, dict[str, Any]] = {}
        self.doors: dict[str, bool] = {}
        self.thermostats: dict[str, float] = {}
        self.security_system: bool = False
        self.logs: list[dict[str, Any]] = []
        self._load()
    
    def _load(self) -> None:
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.rooms = data.get("rooms", {})
                self.doors = data.get("doors", {})
                self.thermostats = data.get("thermostats", {})
                self.security_system = data.get("security_system", False)
                self.logs = data.get("logs", [])
        except (FileNotFoundError, json.JSONDecodeError):
            self.rooms = {}
            self.doors = {}
            self.thermostats = {}
            self.security_system = False
            self.logs = []
    
    def _save(self) -> None:
        data = {
            "rooms": self.rooms,
            "doors": self.doors,
            "thermostats": self.thermostats,
            "security_system": self.security_system,
            "logs": self.logs
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _log(self, action: str) -> None:
        self.logs.append({
            "action": action,
            "timestamp": datetime.now().isoformat()
        })
        self._save()
    
    def toggle_light(self, room_name: str, state: str) -> str:
        if room_name not in self.rooms:
            self.rooms[room_name] = {}
        state_lower = state.lower()
        if state_lower not in ("on", "off"):
            return f"Invalid state '{state}'. Use 'on' or 'off'."
        self.rooms[room_name]["light"] = state_lower == "on"
        self._log(f"Light in {room_name} turned {state_lower}")
        return f"Light in {room_name} is now {state_lower}"
    
    def lock_door(self, door_name: str) -> str:
        if door_name not in self.doors:
            self.doors[door_name] = False
        if self.doors[door_name]:
            return f"{door_name} is already locked"
        self.doors[door_name] = True
        self._log(f"Door {door_name} locked")
        return f"{door_name} is now locked"
    
    def unlock_door(self, door_name: str) -> str:
        if door_name not in self.doors:
            self.doors[door_name] = False
        if not self.doors[door_name]:
            return f"{door_name} is already unlocked"
        self.doors[door_name] = False
        self._log(f"Door {door_name} unlocked")
        return f"{door_name} is now unlocked"
    
    def adjust_thermostat(self, zone: str, temperature: float) -> str:
        if temperature < 60 or temperature > 85:
            return f"Invalid temperature {temperature}°F. Must be between 60-85."
        self.thermostats[zone] = temperature
        self._log(f"Thermostat for {zone} set to {temperature}°F")
        return f"Thermostat for {zone} set to {temperature}°F"
    
    def check_security_system(self) -> str:
        status = "armed" if self.security_system else "disarmed"
        return f"Security system is {status} and all sensors are normal"
    
    def arm_security(self) -> str:
        self.security_system = True
        self._log("Security system armed")
        return "Security system armed"
    
    def disarm_security(self) -> str:
        self.security_system = False
        self._log("Security system disarmed")
        return "Security system disarmed"


# Initialize persistent home instance
home = Home()


logger = logging.getLogger(__name__)

@tool
def toggle_light(room_name: str, state: str) -> str:
    """Toggle the light in a room. Accepts 'on' or 'off'."""
    return home.toggle_light(room_name, state)


@tool
def lock_door(door_name: str) -> str:
    """Lock a specific door"""
    return home.lock_door(door_name)


@tool
def unlock_door(door_name: str) -> str:
    """Unlock a specific door"""
    return home.unlock_door(door_name)


@tool
def adjust_thermostat(zone: str, temperature: float) -> str:
    """Adjust the temperature for a specific zone. Accepts 60-85°F."""
    return home.adjust_thermostat(zone, temperature)


@tool
def check_security_system() -> str:
    """Check the status of the security system"""
    return home.check_security_system()


@tool
def get_environment_details() -> dict[str, Any]:
    """Get current environment details including time, timezone"""
    now = datetime.now(pytz.timezone('Asia/Kolkata'))
    return {
        "current_time": now.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "timezone": "Asia/Kolkata",
        "hour": now.hour,
        "is_night": now.hour < 6 or now.hour > 20,
        "is_morning": 6 <= now.hour < 12,
        "is_afternoon": 12 <= now.hour < 18,
        "is_evening": 18 <= now.hour < 22
    }


tools = [toggle_light, lock_door, unlock_door, adjust_thermostat, check_security_system, get_environment_details]

llm = get_llm("cyankiwi/Qwen3.5-4B-AWQ-4bit", 0, "http://10.193.0.48:8000/v1")

middleware = HumanInTheLoopMiddleware(
    interrupt_on={
        "toggle_light": False,  # All decisions allowed (approve, edit, reject)
        "lock_door": False,
        "unlock_door": False,
        "adjust_thermostat": True,
        "check_security_system": False,  # Safe operation, no approval needed
        "get_environment_details": False,
    },
    description_prefix="Tool execution pending approval",
)

memory = InMemorySaver()

agent = create_agent(
    llm,
    tools,
    checkpointer=memory,
    middleware=[middleware],
    system_prompt = (
        "You are a home automation assistant. You can control lights, door locks, "
        "thermostats, and the security system. You also have access to current "
        "environment details like time of day and timezone. Use this information "
        "to make context-aware suggestions. Use the available tools to fulfill "
        "user requests. Always confirm the actions you've taken.\n\n"
        "Example:\n"
        "<environment_details>\n"
        "Current time: 2026-04-26T03:17:45+05:30\n"
        "Timezone: Asia/Kolkata\n"
        "Hour: 3\n"
        "Is night: True\n"
        "Is morning: False\n"
        "Is afternoon: False\n"
        "Is evening: False\n"
        "</environment_details>\n"
        "Given this, suggest turning off lights and ensuring doors are locked."
    ),
)

user_queries = [
    "I'm going to bed, can you turn off the living room lights and turn on the bedroom lights?",
    "Lock the front door and set the thermostat to 72°F in the living room.",
    "Check if the security system is armed and turn all lights off.",
    "Unlock the back door, turn on the kitchen lights, and set temperature to 68°F.",
    "Good morning! Turn on all lights, unlock the front door, and set thermostat to 70°F.",
    "Based on the current environment, what time-based lighting adjustments should I make?",
    "It's evening time - should the security system be armed?",
    "What's the current environment status and suggested actions?",
    "Environment says it's 3:17 AM - I'm sleeping. Make sure all lights are off, doors are locked, and security is armed."
]


def run() -> None:
    usage_callback = UsageMetadataCallbackHandler()
    metrics_handler = LlmCallMetricsHandler()
    config = {
        "configurable": {"thread_id": "home_automation_session"},
        "run_name": "toggle_light",
        "tags": ["light_toggler", "tool-calling"],
        "callbacks": [usage_callback, metrics_handler],
    }

    for i, query in enumerate(user_queries, 1):
        logger.info("Processing query %d/%d: %s", i, len(user_queries), query)
        result = agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config=config,
        )

        if usage_callback.usage_metadata:
            logger.info("cumulative_usage_by_model=%s", usage_callback.usage_metadata)
        for message in result["messages"]:
            if hasattr(message, "pretty_print"):
                message.pretty_print()
            else:
                print(message)
    

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()