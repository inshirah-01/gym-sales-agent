from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage

from app.config import settings
from app.agents.prompts import MAIN_AGENT_SYSTEM_PROMPT
from app.tools.intent_classifier import intent_classifier
from app.tools.calendly_tool import get_availability_tool, book_trial_tool
from app.tools.gym_info_tool import gym_info_tool

class MainSalesAgent:
    """
    Main sales agent that handles all user interactions
    Uses intent classification to adapt behavior dynamically
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            openai_api_key=settings.openai_api_key
        )
        
        # Tools available to the agent
        self.tools = [
            get_availability_tool,
            book_trial_tool,
            gym_info_tool
        ]
        
        # Agent prompt with intent awareness
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", MAIN_AGENT_SYSTEM_PROMPT),
            ("system", "Current user intent level: {intent_level}"),
            ("system", "Intent reasoning: {intent_reasoning}"),
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
            max_iterations=15
        )
        
        # Session storage (in production, use Redis or similar)
        self.sessions = {}
    
    def _get_or_create_session(self, session_id: str) -> dict:
        """Get or create a session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "chat_history": [],
                "last_intent": "low",
                "user_info": {}
            }
        return self.sessions[session_id]
    
    def _format_chat_history(self, chat_history: list) -> str:
        """Format chat history as string for intent classifier"""
        if not chat_history:
            return ""
        
        formatted = []
        for msg in chat_history[-6:]:  # Last 3 exchanges
            if isinstance(msg, HumanMessage):
                formatted.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                formatted.append(f"Agent: {msg.content}")
        
        return "\n".join(formatted)
    
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
            
            # Step 1: Classify intent
            chat_history_str = self._format_chat_history(session["chat_history"])
            intent_result = await intent_classifier.classify_intent(
                user_message=user_message,
                conversation_history=chat_history_str
            )
            
            # Update session with new intent
            session["last_intent"] = intent_result.intent_level
            
            print(f"\n{'='*50}")
            print(f"[MAIN AGENT] Processing message for session: {session_id}")
            print(f"[MAIN AGENT] User message: {user_message}")
            print(f"[MAIN AGENT] Classified intent: {intent_result.intent_level}")
            print(f"[MAIN AGENT] Intent reasoning: {intent_result.reasoning}")
            print(f"{'='*50}\n")
            
            # Step 2: Run main agent with intent context
            response = await self.agent_executor.ainvoke({
                "input": user_message,
                "chat_history": session["chat_history"],
                "intent_level": intent_result.intent_level.upper(),
                "intent_reasoning": intent_result.reasoning
            })
            
            # Step 3: Update chat history
            session["chat_history"].append(HumanMessage(content=user_message))
            session["chat_history"].append(AIMessage(content=response["output"]))
            
            # Keep only last 10 messages to prevent context overflow
            if len(session["chat_history"]) > 10:
                session["chat_history"] = session["chat_history"][-10:]
            
            # Check if booking was made
            booking_made = "booking" in response["output"].lower() and "confirmed" in response["output"].lower()
            
            return {
                "response": response["output"],
                "session_id": session_id,
                "intent_level": intent_result.intent_level,
                "booking_made": booking_made
            }
            
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            return {
                "response": "I apologize, I encountered an error. Could you please rephrase your message?",
                "session_id": session_id,
                "intent_level": "low",
                "booking_made": False,
                "error": str(e)
            }
    
    def reset_session(self, session_id: str):
        """Reset a session (clear history)"""
        if session_id in self.sessions:
            del self.sessions[session_id]

# Singleton instance
main_agent = MainSalesAgent()