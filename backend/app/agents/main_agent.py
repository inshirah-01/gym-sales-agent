from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage

from app.config import settings
from app.agents.prompts import MAIN_AGENT_SYSTEM_PROMPT
from app.tools.intent_classifier_tool import intent_classifier_tool
from app.tools.calendly_tool import get_availability_tool, book_trial_tool
from app.tools.gym_info_tool import gym_info_tool
from app.tools.memory_tool import memory_update_tool
from app.services.mongodb_service import mongodb_service

class MainSalesAgent:
    """
    Main sales agent that handles all user interactions
    Agent calls intent_classifier_tool to adapt behavior dynamically
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            openai_api_key=settings.openai_api_key
        )
        
        # Tools available to the agent
        self.tools = [
            intent_classifier_tool,  # Agent will call this first
            memory_update_tool,    
            get_availability_tool,
            book_trial_tool,
            gym_info_tool
        ]
        
        # Agent prompt - intent will be determined by tool call
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", MAIN_AGENT_SYSTEM_PROMPT),
            ("system", "CURRENT LEAD PROFILE:\n{memory_context}"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create the agent
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=20,
            return_intermediate_steps=True
        )
        
        # Session storage (in production, use Redis or similar)
        self.sessions = {}
    
    def _get_or_create_session(self, session_id: str) -> dict:
        """Get or create a session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "chat_history": [],
                "last_intent": "unknown",
                "user_info": {},
                "message_count": 0
            }
        return self.sessions[session_id]
    
    def _format_chat_history(self, chat_history: list) -> str:
        """Format chat history as string"""
        if not chat_history:
            return "No previous conversation"
        
        formatted = []
        for msg in chat_history[-6:]:  # Last 3 exchanges
            if isinstance(msg, HumanMessage):
                formatted.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                formatted.append(f"Agent: {msg.content}")
        
        return "\n".join(formatted)
    
    async def _load_memory_context(self, session_id: str) -> str:
        """Load memory from MongoDB and format for agent context"""
        try:
            memory = await mongodb_service.get_memory(session_id)
            
            if not memory:
                return "New lead - no previous information."
            
            # Check if this is actually a new lead (all Unknown)
            is_new = all(
                memory.get(field) in ["Unknown", "None", "unknown"]
                for field in ["fitness_goals", "past_experience", "location_proximity", 
                             "joining_timeline", "motivation", "preferred_time"]
            )
            
            if is_new:
                return "New lead - no previous information."
            
            # Format memory for agent
            context = f"""
Fitness Goals: {memory.get('fitness_goals', 'Unknown')}
Past Experience: {memory.get('past_experience', 'Unknown')}
Location: {memory.get('location_proximity', 'Unknown')}
Timeline: {memory.get('joining_timeline', 'Unknown')}
Motivation: {memory.get('motivation', 'Unknown')}
Preferred Time: {memory.get('preferred_time', 'Unknown')}
Health Info: {memory.get('health_physical_info', 'Unknown')}
Objections: {memory.get('objections', 'None')}

Additional Context: {memory.get('conversation_summary', 'None')}

💡 Use this information to personalize your conversation. Don't ask for details we already know!
"""
            
            print(f"✅ Loaded memory for session: {session_id}")
            return context
            
        except Exception as e:
            print(f"Error loading memory: {str(e)}")
            return "New lead - no previous information."
    
    async def process_message(self, user_message: str, session_id: str) -> dict:
        """Process a user message with memory support"""
        try:
            # Get or create session
            session = self._get_or_create_session(session_id)
            session["message_count"] += 1
            
            # Load memory context
            memory_context = await self._load_memory_context(session_id)
            
            print(f"\n{'='*50}")
            print(f"[MAIN AGENT] Session: {session_id}")
            print(f"[MAIN AGENT] Message #{session['message_count']}: {user_message}")
            print(f"{'='*50}\n")
            
            # Agent processes with memory context
            # Add session_id to input so agent can use it in tool calls
            enriched_input = f"[Session ID: {session_id}]\n{user_message}"

            response = await self.agent_executor.ainvoke({
                         "input": enriched_input,
                         "chat_history": session["chat_history"],
                         "memory_context": memory_context
            })
            
            # Extract intent from intermediate steps
            intent_level = "unknown"
            if response.get("intermediate_steps"):
                for action, observation in response["intermediate_steps"]:
                    if action.tool == "classify_user_intent":
                        try:
                            import json
                            intent_data = json.loads(observation)
                            intent_level = intent_data.get("intent_level", "unknown")
                            session["last_intent"] = intent_level
                            print(f"[INTENT] {intent_level}")
                        except:
                            pass
            
            # Update chat history
            session["chat_history"].append(HumanMessage(content=user_message))
            session["chat_history"].append(AIMessage(content=response["output"]))
            
            # Keep only last 10 messages
            if len(session["chat_history"]) > 10:
                session["chat_history"] = session["chat_history"][-10:]
            
            # Check if booking was made
            booking_made = "booked" in response["output"].lower() or "confirmed" in response["output"].lower()
            
            return {
                "response": response["output"],
                "session_id": session_id,
                "intent_level": intent_level,
                "booking_made": booking_made,
                "message_count": session["message_count"]
            }
            
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                "response": "I apologize, I encountered a technical issue. Could you please try again?",
                "session_id": session_id,
                "intent_level": "unknown",
                "booking_made": False,
                "error": str(e)
            }
    
    def reset_session(self, session_id: str):
        """Reset a session (clear history)"""
        if session_id in self.sessions:
            del self.sessions[session_id]

# Singleton instance
main_agent = MainSalesAgent()
