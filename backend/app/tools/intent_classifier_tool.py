from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.tools import Tool
from app.models.schemas import IntentClassification
from app.agents.prompts import INTENT_CLASSIFIER_PROMPT
from app.config import settings
import json
import asyncio

class IntentClassifierAgent:
    """
    Tool-style agent that classifies user intent
    Called by the main agent to understand customer interest level
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=settings.openai_api_key
        )
        
        self.parser = PydanticOutputParser(pydantic_object=IntentClassification)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", INTENT_CLASSIFIER_PROMPT),
            ("human", """Previous conversation context (if any):
{conversation_history}

Latest user message:
{user_message}

{format_instructions}""")
        ])
    
    async def classify_intent(
        self,
        user_message: str,
        conversation_history: str = ""
    ) -> IntentClassification:
        """
        Classify user intent based on their message and conversation history
        
        Args:
            user_message: The latest message from user
            conversation_history: Previous conversation context
            
        Returns:
            IntentClassification with level, reasoning, and indicators
        """
        try:
            # Format the prompt
            formatted_prompt = self.prompt.format_messages(
                user_message=user_message,
                conversation_history=conversation_history or "No previous context",
                format_instructions=self.parser.get_format_instructions()
            )
            
            # Get classification
            response = await self.llm.ainvoke(formatted_prompt)
            
            # Parse the response
            intent = self.parser.parse(response.content)
            
            print(f"[INTENT CLASSIFIER] Level: {intent.intent_level}")
            print(f"[INTENT CLASSIFIER] Reasoning: {intent.reasoning}")
            
            return intent
            
        except Exception as e:
            print(f"Error in intent classification: {str(e)}")
            # Default to medium intent on error
            return IntentClassification(
                intent_level="medium",
                reasoning="Unable to classify intent, defaulting to medium",
                key_indicators=["classification_error"]
            )

# Singleton instance
intent_classifier = IntentClassifierAgent()

# Create SYNC wrapper for the tool
def classify_intent_sync(input_str: str) -> str:
    """Synchronous wrapper for intent classification"""
    try:
        # Parse input if it's JSON, otherwise use as-is
        if input_str.startswith('{'):
            data = json.loads(input_str)
            user_message = data.get('user_message', input_str)
            conversation_history = data.get('conversation_history', '')
        else:
            user_message = input_str
            conversation_history = ''
        
        # Run async function in sync context
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            intent_classifier.classify_intent(user_message, conversation_history)
        )
        
        return json.dumps({
            "intent_level": result.intent_level,
            "reasoning": result.reasoning,
            "key_indicators": result.key_indicators
        })
    except Exception as e:
        return json.dumps({
            "intent_level": "medium",
            "reasoning": f"Error: {str(e)}",
            "key_indicators": []
        })

# Create the tool wrapper
intent_classifier_tool = Tool(
    name="classify_user_intent",
    description="Classify user's intent level (high/medium/low) based on their message. Call this first for every user message.",
    func=classify_intent_sync
)