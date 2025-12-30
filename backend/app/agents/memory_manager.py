from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.config import settings
from typing import Dict
import json

class MemoryManagerAgent:
    """
    Separate agent responsible for updating lead memory
    Receives current memory + latest conversation and returns updated fields
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=settings.openai_api_key
        )
        
        # Import prompt from prompts.py
        from app.agents.prompts import MEMORY_MANAGER_PROMPT
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", MEMORY_MANAGER_PROMPT),
            ("human", """CURRENT MEMORY:
{current_memory}

USER'S LATEST MESSAGE:
{user_message}

AGENT'S RESPONSE:
{agent_response}

RECENT CONVERSATION HISTORY:
{conversation_history}

---

Based on the above information, generate the UPDATED MEMORY following the exact structure provided in your instructions. Remember:
- Preserve all existing confirmed information
- Only add/update fields with NEW information from this conversation
- Use "Unknown" for fields never discussed
- Use "None" for objections if none raised
- Update conversation_summary with any meaningful new context (keep it concise)

Return ONLY the updated memory in the specified format.""")
        ])
    
    async def update_memory(
        self,
        current_memory: Dict,
        user_message: str,
        agent_response: str,
        conversation_history: str = ""
    ) -> Dict:
        """
        Update memory based on new conversation
        
        Args:
            current_memory: Existing memory document
            user_message: Latest message from user
            agent_response: Latest response from agent
            conversation_history: Recent conversation context
            
        Returns:
            Updated memory dictionary
        """
        try:
            # Format current memory as text
            current_memory_text = f"""
Fitness Goal(s): {current_memory.get('fitness_goals', 'Unknown')}
Past Experience / Background: {current_memory.get('past_experience', 'Unknown')}
Location / Proximity: {current_memory.get('location_proximity', 'Unknown')}
Joining Timeline: {current_memory.get('joining_timeline', 'Unknown')}
Motivation: {current_memory.get('motivation', 'Unknown')}
Preferred Time: {current_memory.get('preferred_time', 'Unknown')}
Health / Physical Info: {current_memory.get('health_physical_info', 'Unknown')}
Objections: {current_memory.get('objections', 'None')}
Other Notes: {current_memory.get('conversation_summary', 'None')}
"""
            
            # Call LLM
            messages = self.prompt.format_messages(
                current_memory=current_memory_text,
                user_message=user_message,
                agent_response=agent_response,
                conversation_history=conversation_history or "No previous conversation"
            )
            
            response = await self.llm.ainvoke(messages)
            
            # Parse the response
            updated_memory = self._parse_memory_response(response.content, current_memory)
            
            print(f"\n[MEMORY MANAGER] Updated fields:")
            for key, value in updated_memory.items():
                if key not in ['_id', 'created_at', 'last_updated', 'total_messages']:
                    if current_memory.get(key) != value:
                        print(f"  - {key}: {current_memory.get(key)} → {value}")
            
            return updated_memory
            
        except Exception as e:
            print(f"[MEMORY MANAGER ERROR] {str(e)}")
            # Return current memory unchanged on error
            return current_memory
    
    def _parse_memory_response(self, response_text: str, current_memory: Dict) -> Dict:
        """
        Parse LLM response into structured memory format
        
        Args:
            response_text: LLM's response text
            current_memory: Current memory to preserve metadata
            
        Returns:
            Updated memory dictionary
        """
        try:
            # Initialize with current memory
            updated = dict(current_memory)
            
            # Parse the structured response
            lines = response_text.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                
                if line.startswith("Fitness Goal(s):"):
                    updated["fitness_goals"] = line.split(":", 1)[1].strip()
                elif line.startswith("Past Experience"):
                    updated["past_experience"] = line.split(":", 1)[1].strip()
                elif line.startswith("Location"):
                    updated["location_proximity"] = line.split(":", 1)[1].strip()
                elif line.startswith("Joining Timeline:"):
                    updated["joining_timeline"] = line.split(":", 1)[1].strip()
                elif line.startswith("Motivation:"):
                    updated["motivation"] = line.split(":", 1)[1].strip()
                elif line.startswith("Preferred Time:"):
                    updated["preferred_time"] = line.split(":", 1)[1].strip()
                elif line.startswith("Health"):
                    updated["health_physical_info"] = line.split(":", 1)[1].strip()
                elif line.startswith("Objections:"):
                    updated["objections"] = line.split(":", 1)[1].strip()
                elif line.startswith("Other Notes:"):
                    updated["conversation_summary"] = line.split(":", 1)[1].strip()
            
            # Preserve metadata
            updated["_id"] = current_memory.get("_id")
            updated["created_at"] = current_memory.get("created_at")
            updated["total_messages"] = current_memory.get("total_messages", 0) + 1
            updated["last_intent"] = current_memory.get("last_intent", "unknown")
            
            return updated
            
        except Exception as e:
            print(f"[MEMORY PARSER ERROR] {str(e)}")
            return current_memory

# Singleton instance
memory_manager = MemoryManagerAgent()