"""
DM Agent using LangChain
This agent acts as the Dungeon Master for the game.
"""
from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
import os


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
        
        self.system_prompt = """You are a creative and engaging Dungeon Master for a text-based D&D-style role-playing game.

Your role is to:
- Create an immersive fantasy adventure experience
- Respond to player actions with vivid descriptions
- Maintain game continuity and narrative flow
- Be creative but fair with outcomes
- Keep responses concise but engaging (2-4 sentences)

Always respond in-character as the DM narrating the story."""
    
    def get_response(self, player_message: str, game_history: List[Dict[str, Any]]) -> str:
        """
        Generate a DM response to a player's message.
        
        Args:
            player_message: The player's current message
            game_history: List of previous game events (for context)
        
        Returns:
            The DM's response string
        """
        # Build message history for context
        messages = [SystemMessage(content=self.system_prompt)]
        
        # Add recent game history (last 10 events for context)
        for event in game_history[-10:]:
            if event.get("type") == "player_message":
                player_id = event.get("payload", {}).get("player_id", "Unknown")
                msg = event.get("payload", {}).get("message", "")
                messages.append(HumanMessage(content=f"Player {player_id}: {msg}"))
            elif event.get("type") == "dm_response":
                msg = event.get("payload", {}).get("message", "")
                messages.append(AIMessage(content=msg))
        
        # Add current player message
        messages.append(HumanMessage(content=player_message))
        
        # Get response from LLM
        response = self.llm.invoke(messages)
        return response.content


# Singleton instance
_dm_agent = None

def get_dm_agent() -> DMAgent:
    """Get or create the singleton DM agent instance"""
    global _dm_agent
    if _dm_agent is None:
        _dm_agent = DMAgent()
    return _dm_agent
