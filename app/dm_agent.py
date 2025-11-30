"""
DM Agent using LangChain
This agent acts as the Dungeon Master for the game.
"""
from typing import List, Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from .models import Character
import os
import json
import random


@tool
def roll_dice(dice_type: str, count: int = 1) -> str:
    """
    Roll one or more dice and return the results.
    Use this for skill checks, combat rolls, damage rolls, or any random events.
    
    Args:
        dice_type: Type of dice (d4, d6, d8, d10, d12, d20, d100)
        count: Number of dice to roll (default 1)
    
    Returns:
        JSON with individual rolls, total, and dice type
    """
    valid_dice = {
        "d4": 4, "d6": 6, "d8": 8, "d10": 10, 
        "d12": 12, "d20": 20, "d100": 100
    }
    
    dice_type_lower = dice_type.lower()
    if dice_type_lower not in valid_dice:
        return json.dumps({"error": f"Invalid dice type. Choose from: {', '.join(valid_dice.keys())}"})
    
    if count < 1 or count > 20:
        return json.dumps({"error": "Count must be between 1 and 20"})
    
    sides = valid_dice[dice_type_lower]
    rolls = [random.randint(1, sides) for _ in range(count)]
    
    return json.dumps({
        "dice_type": dice_type_lower,
        "count": count,
        "rolls": rolls,
        "total": sum(rolls)
    })


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
    base_hp = 10 + constitution
    character = {
        "name": name,
        "class_type": class_type,
        "level": 1,
        "experience": 0,
        "strength": strength,
        "dexterity": dexterity,
        "constitution": constitution,
        "intelligence": intelligence,
        "wisdom": wisdom,
        "charisma": charisma,
        "hit_points": base_hp,
        "max_hit_points": base_hp,
        "backstory": backstory
    }
    return json.dumps(character)


@tool
def grant_experience(amount: int, reason: str = "") -> str:
    """
    Grant experience points to the player's character.
    Use this when the player defeats enemies, completes quests, or performs heroic actions.
    
    Args:
        amount: Experience points to grant (typically 10-100 per encounter)
        reason: Why experience is being granted (e.g., "defeated goblin", "solved puzzle")
    
    Returns:
        JSON with experience granted and reason
    """
    return json.dumps({"experience": amount, "reason": reason})


@tool
def level_up_character(
    attribute_to_increase: str,
    hp_increase: int = 5
) -> str:
    """
    Level up a character when they have enough experience.
    Experience needed: 100 * current_level
    
    Args:
        attribute_to_increase: Which attribute to increase (strength, dexterity, constitution, intelligence, wisdom, charisma)
        hp_increase: How much to increase max HP (default 5)
    
    Returns:
        JSON with level up details
    """
    valid_attributes = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
    if attribute_to_increase.lower() not in valid_attributes:
        return json.dumps({"error": f"Invalid attribute. Choose from: {', '.join(valid_attributes)}"})
    
    return json.dumps({
        "level_up": True,
        "attribute_increased": attribute_to_increase.lower(),
        "hp_increase": hp_increase
    })


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
        self.llm_with_tools = self.llm.bind_tools([create_character, grant_experience, level_up_character, roll_dice])
        
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

EXPERIENCE & LEVELING:
- Grant experience using grant_experience tool when players defeat enemies, solve puzzles, or complete quests
- Typical experience rewards: minor encounter (10-30 XP), significant encounter (50-100 XP), major victory (150-300 XP)
- Players level up when experience >= 100 * current_level
- IMPORTANT: First grant XP, then check if they can level up. The system will apply XP before checking level up requirements.
- When player has enough total XP to level up (after granting new XP), use level_up_character tool
- Let the player choose which attribute to increase when leveling up
- Leveling up increases: chosen attribute by 1, max HP by 5, and fully restores current HP
- You can grant XP and trigger level up in the same response if the new XP total reaches the threshold

DICE ROLLING:
- Use roll_dice tool for skill checks, combat rolls, saving throws, and damage
- Common rolls: d20 for skill checks/attacks, d6-d12 for damage, d4 for small weapons
- You can roll multiple dice at once (e.g., 2d6 for damage)
- Always narrate the result dramatically based on the roll
- High rolls (15+) are successes, low rolls (5-) are failures for skill checks

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
            messages.append(SystemMessage(content=f"IMPORTANT: Player {player_id} already has a character: {char.get('name', 'Unknown')}, a level {char.get('level', 1)} {char.get('class_type', 'Unknown')} with {char.get('experience', 0)} XP. DO NOT create a new character. Begin or continue their adventure."))
        
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
        
        result = {"message": response.content or ""}
        
        # Check if tools were called
        if hasattr(response, "tool_calls") and response.tool_calls:
            # Add the AI response with tool calls to messages
            messages.append(response)
            
            # Execute all tool calls and add tool messages
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_call_id = tool_call["id"]
                tool_output = None
                
                if tool_name == "create_character":
                    # Execute the tool
                    char_json = create_character.invoke(tool_call["args"])
                    result["character"] = json.loads(char_json)
                    tool_output = char_json
                
                elif tool_name == "grant_experience":
                    xp_data = json.loads(grant_experience.invoke(tool_call["args"]))
                    result["experience"] = xp_data["experience"]
                    tool_output = json.dumps(xp_data)
                
                elif tool_name == "level_up_character":
                    levelup_data = json.loads(level_up_character.invoke(tool_call["args"]))
                    if "error" not in levelup_data:
                        result["level_up"] = True
                        result["attribute_increased"] = levelup_data["attribute_increased"]
                        result["hp_increase"] = levelup_data["hp_increase"]
                    tool_output = json.dumps(levelup_data)
                
                elif tool_name == "roll_dice":
                    dice_data = json.loads(roll_dice.invoke(tool_call["args"]))
                    tool_output = json.dumps(dice_data)
                
                # Add tool message with the result
                if tool_output:
                    messages.append(ToolMessage(content=tool_output, tool_call_id=tool_call_id))
            
            # Get the final narrative response from the LLM
            final_response = self.llm_with_tools.invoke(messages)
            result["message"] = final_response.content or "Something interesting happened..."
        
        return result


# Singleton instance
_dm_agent = None

def get_dm_agent() -> DMAgent:
    """Get or create the singleton DM agent instance"""
    global _dm_agent
    if _dm_agent is None:
        _dm_agent = DMAgent()
    return _dm_agent
