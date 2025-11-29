"""
DM Agent using LangChain
This agent acts as the Dungeon Master for the game.
"""
from typing import List, Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from .models import Character
import os
import json


@tool
def create_character(
    name: str,
    class_type: str,
    strength: int = 10,
    dexterity: int = 10,
    constitution: int = 10,
    intelligence: int = 10,
    wisdom: int = 10,
    charisma: int = 10,
    backstory: str = ""
) -> str:
    """
    Create a D&D character with name, class, and attributes.
    
    Args:
        name: Character name
        class_type: Character class (Warrior, Mage, Rogue, Cleric, Ranger, Paladin, etc.)
        strength: Strength attribute (default 10)
        dexterity: Dexterity attribute (default 10)
        constitution: Constitution attribute (default 10)
        intelligence: Intelligence attribute (default 10)
        wisdom: Wisdom attribute (default 10)
        charisma: Charisma attribute (default 10)
        backstory: Character backstory (optional)
    
    Returns:
        JSON string with character details
    """
    character = {
        "name": name,
        "class_type": class_type,
        "level": 1,
        "strength": strength,
        "dexterity": dexterity,
        "constitution": constitution,
        "intelligence": intelligence,
        "wisdom": wisdom,
        "charisma": charisma,
        "hit_points": 10 + constitution,  # Base HP + CON modifier
        "backstory": backstory
    }
    return json.dumps(character)


class DMAgent:
    """Dungeon Master agent powered by LangChain"""
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        """
        Initialize the DM agent.
        
        Args:
            model_name: The model to use (default: gpt-4o-mini)
        """
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.7,
            api_key=os.getenv("GITHUB_TOKEN"),
            base_url="https://models.inference.ai.azure.com"
        )
        
        # Bind tools to the LLM
        self.llm_with_tools = self.llm.bind_tools([create_character])
        
        self.system_prompt = """You are a creative and engaging Dungeon Master for a text-based D&D-style role-playing game.

Your role is to:
- Create an immersive fantasy adventure experience
- Guide players through character creation if they don't have a character yet
- For character creation, use the create_character tool to set up their character sheet
- Ask players for their preferred character class, name, and optionally attributes and backstory
- Once a character is created, begin the adventure
- Respond to player actions with vivid descriptions
- Maintain game continuity and narrative flow
- Be creative but fair with outcomes
- Keep responses concise but engaging (2-4 sentences)

IMPORTANT: If a player hasn't created a character yet, guide them through character creation first before starting the adventure.

Always respond in-character as the DM narrating the story."""
    
    def get_response(self, player_message: str, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a DM response to a player's message.
        
        Args:
            player_message: The player's current message
            game_state: Complete game state including history and characters
        
        Returns:
            Dict with 'message' and optionally 'character' if one was created
        """
        player_id = game_state.get("current_player_id", "unknown")
        has_character = game_state.get("characters", {}).get(player_id) is not None
        game_history = game_state.get("history", [])
        
        # Build message history for context
        messages = [SystemMessage(content=self.system_prompt)]
        
        # Add character status context
        if not has_character:
            messages.append(SystemMessage(content=f"Player {player_id} does not have a character yet. Guide them through character creation."))
        else:
            char = game_state.get("characters", {}).get(player_id, {})
            messages.append(SystemMessage(content=f"Player {player_id} is playing as {char.get('name', 'Unknown')}, a level {char.get('level', 1)} {char.get('class_type', 'Unknown')}."))
        
        # Add recent game history (last 10 events for context)
        for event in game_history[-10:]:
            if event.get("type") == "player_message":
                pid = event.get("payload", {}).get("player_id", "Unknown")
                msg = event.get("payload", {}).get("message", "")
                messages.append(HumanMessage(content=f"Player {pid}: {msg}"))
            elif event.get("type") == "dm_response":
                msg = event.get("payload", {}).get("message", "")
                messages.append(AIMessage(content=msg))
        
        # Add current player message
        messages.append(HumanMessage(content=player_message))
        
        # Get response from LLM with tools
        response = self.llm_with_tools.invoke(messages)
        
        result = {"message": response.content}
        
        # Check if tool was called (character creation)
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call["name"] == "create_character":
                    # Execute the tool
                    char_json = create_character.invoke(tool_call["args"])
                    result["character"] = json.loads(char_json)
                    result["message"] = f"Character created! Welcome, {result['character']['name']} the {result['character']['class_type']}! Your adventure begins..."
        
        return result


# Singleton instance
_dm_agent = None

def get_dm_agent() -> DMAgent:
    """Get or create the singleton DM agent instance"""
    global _dm_agent
    if _dm_agent is None:
        _dm_agent = DMAgent()
    return _dm_agent
