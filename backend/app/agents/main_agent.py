from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage

from app.config import settings
from app.agents.prompts import MAIN_AGENT_SYSTEM_PROMPT
from app.tools.intent_classifier_tool import intent_classifier_tool
from app.tools.calendly_tool import get_availability_tool, book_trial_tool
from app.tools.gym_info_tool import gym_info_tool

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
            get_availability_tool,
            book_trial_tool,
            gym_info_tool
        ]
        
        # Agent prompt - intent will be determined by tool call
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", MAIN_AGENT_SYSTEM_PROMPT),
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
                "user_info": {}
            }
        return self.sessions[session_id]
    
    async def process_message(self, user_message: str, session_id: str) -> dict:
        """
        Process a user message and return response
        
        Args:
            user_message: The user's message
            session_id: Session identifier
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Get or create session
            session = self._get_or_create_session(session_id)
            
            print(f"\n{'='*50}")
            print(f"[MAIN AGENT] Processing message for session: {session_id}")
            print(f"[MAIN AGENT] User message: {user_message}")
            print(f"{'='*50}\n")
            
            # Agent will call intent_classifier_tool as first action
            response = await self.agent_executor.ainvoke({
                "input": user_message,
                "chat_history": session["chat_history"]
            })
            
            # Extract intent from intermediate steps if available
            intent_level = "unknown"
            if response.get("intermediate_steps"):
                for action, observation in response["intermediate_steps"]:
                    if action.tool == "classify_user_intent":
                        try:
                            import json
                            intent_data = json.loads(observation)
                            intent_level = intent_data.get("intent_level", "unknown")
                            session["last_intent"] = intent_level
                            print(f"[INTENT DETECTED] {intent_level}")
                        except:
                            pass
            
            # Update chat history
            session["chat_history"].append(HumanMessage(content=user_message))
            session["chat_history"].append(AIMessage(content=response["output"]))
            
            # Keep only last 10 messages to prevent context overflow
            if len(session["chat_history"]) > 10:
                session["chat_history"] = session["chat_history"][-10:]
            
            # Check if booking was made
            booking_made = "booked" in response["output"].lower() or "confirmed" in response["output"].lower()
            
            return {
                "response": response["output"],
                "session_id": session_id,
                "intent_level": intent_level,
                "booking_made": booking_made
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