"""
Weather & Wardrobe Agent

This agent retrieves real-time weather data from OpenWeatherMap API,
reads a local wardrobe inventory file, and recommends appropriate outfits
based on current conditions using the ReAct pattern.

Learning Objectives:
    - Real API authentication with environment variables
    - Parsing large JSON payloads from external APIs
    - Handling network timeouts and retry logic
    - ReAct agent pattern with LangChain
    - Human-in-the-loop middleware for tool approval

Prerequisites:
    1. Get an API key from https://openweathermap.org/api
    2. Set environment variable: export OPENWEATHER_API_KEY="your_key"
    3. Create my_closet.txt with clothing items (see sample format)

Usage:
    python weather_wardrobe_agent.py
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain.tools import tool
from langchain_core.messages import AIMessage
from langchain_core.callbacks import UsageMetadataCallbackHandler

from langgraph.checkpoint.memory import InMemorySaver

from utility import LlmCallMetricsHandler, get_llm

logger = logging.getLogger(__name__)


@dataclass
class WeatherService:
    """Handles OpenWeatherMap API calls with authentication, timeouts, and retries."""
    
    api_key: str
    base_url: str = "https://api.openweathermap.org/data/2.5"
    timeout: int = 10
    max_retries: int = 3
    
    def __post_init__(self) -> None:
        if not self.api_key:
            raise ValueError(
                "OPENWEATHER_API_KEY environment variable not set. "
                "Get a free key at https://openweathermap.org/api"
            )
    
    def get_current_weather(self, city: str, units: str = "imperial") -> dict[str, Any]:
        """
        Fetch current weather for a city.
        
        Args:
            city: City name, optionally with country code (e.g., "Chicago,US")
            units: "imperial" (°F) or "metric" (°C)
            
        Returns:
            Dict with weather data including temp, conditions, humidity, wind
            
        Raises:
            requests.RequestException: On network errors
            ValueError: On invalid API responses
        """
        url = f"{self.base_url}/weather"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": units,
        }
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug("Fetching weather for %s (attempt %d/%d)", city, attempt, self.max_retries)
                response = requests.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                parsed = self._parse_weather_response(data)
                logger.info("Weather fetched for %s: %s°F, %s", city, parsed["temp"], parsed["description"])
                return parsed
                
            except requests.exceptions.Timeout:
                logger.warning("Timeout fetching weather for %s (attempt %d)", city, attempt)
                if attempt == self.max_retries:
                    raise
            except requests.exceptions.RequestException as e:
                logger.error("API request failed: %s", e)
                raise ValueError(f"Failed to fetch weather: {e}")
            except (KeyError, json.JSONDecodeError) as e:
                logger.error("Invalid API response: %s", e)
                raise ValueError(f"Invalid weather data format: {e}")
        
        raise RuntimeError("Unreachable")
    
    def _parse_weather_response(self, data: dict[str, Any]) -> dict[str, Any]:
        """Extract only the needed fields from OpenWeatherMap response."""
        if "main" not in data or "weather" not in data:
            raise ValueError("Missing required weather fields")
        
        main = data["main"]
        weather = data["weather"][0]
        wind = data.get("wind", {})
        
        return {
            "city": data.get("name", "Unknown"),
            "temp": round(main.get("temp", 0)),
            "feels_like": round(main.get("feels_like", 0)),
            "temp_min": round(main.get("temp_min", 0)),
            "temp_max": round(main.get("temp_max", 0)),
            "humidity": main.get("humidity", 0),
            "pressure": main.get("pressure", 0),
            "description": weather.get("description", "unknown").title(),
            "wind_speed": wind.get("speed", 0),
            "wind_deg": wind.get("deg", 0),
            "clouds": data.get("clouds", {}).get("all", 0),
            "sunrise": datetime.fromtimestamp(data.get("sys", {}).get("sunrise", 0)).strftime("%H:%M"),
            "sunset": datetime.fromtimestamp(data.get("sys", {}).get("sunset", 0)).strftime("%H:%M"),
        }


class WardrobeManager:
    """Manages closet inventory from my_closet.txt."""
    
    def __init__(self, filepath: str = "my_closet.txt"):
        self.filepath = filepath
        self._clothes: dict[str, dict[str, Any]] = {}
        self._load()
    
    def _load(self) -> None:
        """Load closet inventory from file."""
        if not os.path.exists(self.filepath):
            logger.warning("Closet file not found: %s. Using empty wardrobe.", self.filepath)
            self._clothes = {}
            return
        
        try:
            with open(self.filepath, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    
                    parts = [p.strip() for p in line.split(":")]
                    if len(parts) < 3:
                        logger.warning("Skipping malformed closet line: %s", line)
                        continue
                    
                    name, category, warmth = parts[0], parts[1], parts[2]
                    notes = parts[3] if len(parts) > 3 else ""
                    self._clothes[name] = {
                        "category": category,
                        "warmth": int(warmth),
                        "notes": notes,
                    }
            
            logger.info("Loaded %d clothing items from %s", len(self._clothes), self.filepath)
            
        except (IOError, ValueError) as e:
            logger.error("Failed to read closet file: %s", e)
            self._clothes = {}
    
    def get_items_by_warmth(self, min_warmth: int = 1, max_warmth: int = 10) -> list[dict[str, Any]]:
        items = []
        for name, data in self._clothes.items():
            if min_warmth <= data["warmth"] <= max_warmth:
                items.append({"name": name, **data})
        return sorted(items, key=lambda x: x["warmth"], reverse=True)
    
    def get_items_by_category(self, category: str) -> list[dict[str, Any]]:
        items = []
        for name, data in self._clothes.items():
            if data["category"].lower() == category.lower():
                items.append({"name": name, **data})
        return items
    
    def all_items(self) -> list[str]:
        return list(self._clothes.keys())


# Lazy initialization helpers
_weather_service: WeatherService | None = None
_wardrobe: WardrobeManager | None = None


def _get_weather_service() -> WeatherService | None:
    global _weather_service
    if _weather_service is None:
        api_key = (os.getenv("OPENWEATHER_API_KEY") or "").strip()
        if not api_key:
            logger.error("OPENWEATHER_API_KEY environment variable not set")
            return None
        try:
            _weather_service = WeatherService(api_key=api_key)
        except Exception as e:
            logger.error("Failed to initialize WeatherService: %s", e)
            return None
    return _weather_service


def _get_wardrobe() -> WardrobeManager:
    global _wardrobe
    if _wardrobe is None:
        _wardrobe = WardrobeManager("my_closet.txt")
    return _wardrobe


@tool
def get_weather(city: str) -> dict[str, Any]:
    """
    Get current weather for a city from OpenWeatherMap API.
    
    Args:
        city: City name with optional country code (e.g., "Chicago,US" or "London")
    
    Returns:
        Dict containing temperature, conditions, humidity, wind speed, etc.
        
    Example:
        {
            "city": "Chicago",
            "temp": 45,
            "description": "Clear Sky",
            "humidity": 65,
            "wind_speed": 8
        }
    """
    service = _get_weather_service()
    if service is None:
        return {
            "error": "Weather service unavailable. Set OPENWEATHER_API_KEY environment variable.",
            "city": city,
            "temp": None,
            "description": "unavailable"
        }
    
    try:
        return service.get_current_weather(city)
    except Exception as e:
        logger.error("Weather fetch error: %s", e)
        return {"error": str(e), "city": city, "temp": None, "description": "unavailable"}


@tool
def read_closet() -> dict[str, Any]:
    """
    Read the local my_closet.txt file and return wardrobe inventory.
    
    Returns:
        Dict with 'items' list and metadata
        
    Example:
        {
            "count": 12,
            "items": [
                {"name": "wool_sweater", "category": "top", "warmth": 5, "notes": "Great for cold days"}
            ]
        }
    """
    try:
        wardrobe = _get_wardrobe()
        items = [
            {"name": name, **data}
            for name, data in wardrobe._clothes.items()
        ]
        return {
            "count": len(items),
            "items": items,
            "filepath": wardrobe.filepath,
        }
    except Exception as e:
        logger.error("Closet read error: %s", e)
        return {"error": str(e), "count": 0, "items": []}


tools = [get_weather, read_closet]

llm = get_llm("cyankiwi/Qwen3.5-4B-AWQ-4bit", 0, "http://10.193.0.48:8000/v1")

middleware = HumanInTheLoopMiddleware(
    interrupt_on={
        "get_weather": False,   # Read-only, safe
        "read_closet": False,   # Read-only, safe
    },
    description_prefix="Tool execution pending approval",
)

memory = InMemorySaver()

SYSTEM_PROMPT = """You are a helpful Weather & Wardrobe assistant. Use the available tools to answer the user.

Guidelines:
- To recommend an outfit, first call get_weather with the city name
- Then call read_closet to see what clothing items are available
- Weather temperature determines needed warmth level:
    * Hot (75°F+): warmth 1-3 (light clothes)
    * Mild (65-74°F): warmth 2-4 (light layers)
    * Cool (50-64°F): warmth 3-6 (medium warmth)
    * Cold (32-49°F): warmth 5-8 (warm clothes)
    * Freezing (<32°F): warmth 7-10 (very warm)
- Consider weather conditions: rain → bring umbrella/raincoat, wind → windbreaker, high humidity → breathable fabrics
- Be specific: mention actual clothing item names from the closet
- If no suitable items exist, clearly state that and suggest what to look for
- Always include both the weather details and reasoning in your final answer"""

agent = create_agent(
    llm,
    tools,
    checkpointer=memory,
    middleware=[middleware],
    system_prompt=SYSTEM_PROMPT,
)

USER_QUERY = "What should I wear today in Chicago?"


def run() -> None:
    """Execute the wardrobe recommendation query with robust error handling."""
    usage_callback = UsageMetadataCallbackHandler()
    metrics_handler = LlmCallMetricsHandler()
    
    config = {
        "configurable": {"thread_id": "wardrobe_session"},
        "run_name": "weather_wardrobe",
        "tags": ["weather", "wardrobe", "tool-calling"],
        "callbacks": [usage_callback, metrics_handler],
    }
    
    logger.info("Weather & Wardrobe Agent - query: %s", USER_QUERY)
    
    # Validate prerequisites before invoking agent
    if _get_weather_service() is None:
        print("ERROR: OPENWEATHER_API_KEY environment variable is not set.")
        print("Get a free API key at https://openweathermap.org/api and run:")
        print("  export OPENWEATHER_API_KEY='your_key_here'")
        return
    
    wardrobe = _get_wardrobe()
    if not wardrobe.all_items():
        print(f"WARNING: Closet file '{wardrobe.filepath}' is empty or missing.")
        print("Create my_closet.txt with your clothing inventory (see example format in the file comments).")
        print("Continuing anyway...\n")
    
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": USER_QUERY}]},
            config=config,
        )
        
        print("\n" + "="*70)
        print("WEATHER & WARDROBE RECOMMENDATION")
        print("="*70)
        final_answer = ""
        for msg in reversed(result.get("messages", [])):
            if isinstance(msg, AIMessage) and msg.content:
                final_answer = (
                    msg.content
                    if isinstance(msg.content, str)
                    else str(msg.content)
                )
                break
        if not final_answer:
            final_answer = result.get("output", str(result))
        print(final_answer)
        print("="*70)
        
        if usage_callback.usage_metadata:
            logger.info("Token usage: %s", usage_callback.usage_metadata)
            
    except requests.exceptions.Timeout:
        logger.error("Weather API timeout after %ds", 10)
        print("ERROR: Weather service timeout. Please try again later.")
    except requests.exceptions.RequestException as e:
        logger.error("Network error: %s", e)
        print(f"ERROR: Network error - {e}")
    except Exception as e:
        logger.error("Agent error: %s", e, exc_info=True)
        print(f"ERROR: {e}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()
