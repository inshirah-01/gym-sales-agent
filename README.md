# Gym Sales Agent - AI-Powered Trial Booking System

An intelligent sales agent that adapts its conversation style based on user intent to help book gym trial sessions.

## 🏗️ Architecture

```
Main Agent (OpenAI GPT-4)
    ├── Intent Classifier Tool (analyzes user interest: high/medium/low)
    ├── Calendly Booking Tool (checks availability & books slots)
    └── Gym Info Tool (retrieves facility/class/trainer information)
```

**Key Design Features:**
- Single main agent handles all user interactions
- Intent classifier runs on every message to adapt agent behavior
- Agent switches between "nurturer" and "closer" modes based on intent
- Generic Calendly service (easily portable to Node.js)

## 📁 Project Structure

```
gym-sales-agent/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app
│   │   ├── config.py                # Environment config
│   │   ├── models/
│   │   │   └── schemas.py           # Pydantic models
│   │   ├── agents/
│   │   │   ├── main_agent.py        # Main sales agent
│   │   │   ├── intent_classifier.py # Intent classification
│   │   │   └── prompts.py           # Agent prompts
│   │   ├── tools/
│   │   │   ├── calendly_tool.py     # Calendly integration
│   │   │   └── gym_info_tool.py     # Gym info retrieval
│   │   └── services/
│   │       └── calendly_service.py  # Calendly API service
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── script.js
└── .env
```

## 🚀 Setup Instructions

### 1. Clone and Setup Environment

```bash
# Create project directory
mkdir gym-sales-agent
cd gym-sales-agent

# Create directory structure
mkdir -p backend/app/{models,agents,tools,services,utils}
mkdir frontend
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the `backend` directory:

```bash
# Copy from .env.example
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Required API Keys:**

1. **OpenAI API Key**
   - Get from: https://platform.openai.com/api-keys
   - Set: `OPENAI_API_KEY=sk-...`

2. **Calendly API Token**
   - Get from: https://calendly.com/integrations/api_webhooks
   - Go to "Personal Access Tokens" → Generate New Token
   - Set: `CALENDLY_API_TOKEN=your_token`

3. **Calendly Event Type URI**
   - Create an event type in Calendly (e.g., "Gym Trial Session")
   - Get the URI from Calendly API or event settings
   - Format: `https://api.calendly.com/event_types/XXXXXXXX`
   - Set: `CALENDLY_EVENT_TYPE_URI=https://...`

### 4. Create Empty `__init__.py` Files

```bash
New-Item .\app\__init__.py -ItemType File
New-Item .\models\__init__.py -ItemType File
New-Item .\agents\__init__.py -ItemType File
New-Item .\tools\__init__.py -ItemType File
New-Item .\services\__init__.py -ItemType File
New-Item .\utils\__init__.py -ItemType File

```

## 🧪 Testing the Application

### Method 1: Run the Complete Application

```bash
# From backend directory
cd backend
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Access the app:**
- Frontend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Method 2: Test Individual Components

#### A. Test Calendly Integration

```bash
# Test availability endpoint
curl http://localhost:8000/test-calendly
```

**Expected Response:**
```json
{
  "success": true,
  "available_slots": 12,
  "slots": [
    {
      "start_time": "2024-01-15T09:00:00",
      "formatted": "January 15, 2024 at 09:00 AM",
      "status": "available"
    }
  ]
}
```

#### B. Test Chat Endpoint (API)

```bash
# Test with low intent message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about the gym"
  }'

# Test with high intent message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to book a trial today",
    "session_id": "test-session-123"
  }'
```

#### C. Test Intent Classification

Create a test script `test_intent.py`:

```python
import asyncio
from app.agents.intent_classifier import intent_classifier

async def test_intent():
    # Test cases
    test_messages = [
        "Just browsing",
        "What facilities do you have?",
        "I want to book a trial right now"
    ]
    
    for msg in test_messages:
        result = await intent_classifier.classify_intent(msg)
        print(f"\nMessage: {msg}")
        print(f"Intent: {result.intent_level}")
        print(f"Reasoning: {result.reasoning}")

asyncio.run(test_intent())
```

Run:
```bash
cd backend
python test_intent.py
```

### Method 3: Interactive Testing via Frontend

1. **Open browser**: http://localhost:8000
2. **Test different intent levels:**

**Low Intent:**
- "Hi there"
- "Tell me about your gym"
- "What equipment do you have?"

**Medium Intent:**
- "I'm thinking about joining a gym"
- "What are your membership plans?"
- "Do you have personal trainers?"

**High Intent:**
- "I want to book a trial"
- "Can I come today?"
- "What times are available this week?"

3. **Watch the intent indicator** change in real-time
4. **Notice behavior changes:**
   - Low → Educational, information-focused
   - Medium → Engaging, value-building
   - High → Action-oriented, booking-focused

### Method 4: Test Complete Booking Flow

```bash
# 1. Start conversation
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to book a trial session"
  }' | jq

# 2. Continue with booking details
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "My name is John Doe and email is john@example.com. Tomorrow morning works.",
    "session_id": "<session_id_from_step_1>"
  }' | jq
```

## 📊 Monitoring & Debugging

### Enable Verbose Logging

The agent has verbose mode enabled. Watch the console for:

```
==================================================
[MAIN AGENT] Processing message for session: abc123
[MAIN AGENT] User message: I want to book a trial
[MAIN AGENT] Classified intent: high
[MAIN AGENT] Intent reasoning: User explicitly requested booking
==================================================

[INTENT CLASSIFIER] Level: high
[INTENT CLASSIFIER] Reasoning: Direct booking request with urgency
```

### Check API Documentation

Visit http://localhost:8000/docs for interactive API documentation

## 🔧 Troubleshooting

### Issue: "Session Error" or "Unauthorized"

**Solution:** Check your `.env` file has correct API keys

```bash
# Verify OpenAI key
python -c "from app.config import settings; print(settings.openai_api_key[:20])"

# Verify Calendly token
python -c "from app.config import settings; print(settings.calendly_api_token[:20])"
```

### Issue: No Available Slots Returned

**Solution:** The app uses mock slots as fallback. To use real Calendly slots:

1. Ensure `CALENDLY_EVENT_TYPE_URI` is correct
2. Check Calendly API token has proper permissions
3. Test endpoint: http://localhost:8000/test-calendly

### Issue: Agent Doesn't Use Tools

**Solution:** Check prompt formatting and tool descriptions. Enable verbose mode:

```python
# In main_agent.py
self.agent_executor = AgentExecutor(
    agent=self.agent,
    tools=self.tools,
    verbose=True,  # Should be True
    ...
)
```

### Issue: Intent Always Shows "Low"

**Solution:** Test intent classifier directly:

```bash
python test_intent.py
```

Check that GPT-4 model is accessible with your API key.

## 🎯 Testing Scenarios

### Scenario 1: Cold Lead (Low Intent)
```
User: "Hi"
Expected: Friendly greeting, asks about fitness goals
Intent: LOW

User: "Just looking around"
Expected: Educational info, no pressure
Intent: LOW
```

### Scenario 2: Warm Lead (Medium Intent)
```
User: "What classes do you offer?"
Expected: Detailed class info, soft nudge toward trial
Intent: MEDIUM

User: "How much is membership?"
Expected: Pricing with value props, trial mention
Intent: MEDIUM → HIGH
```

### Scenario 3: Hot Lead (High Intent)
```
User: "I want to book a trial today"
Expected: Immediate action, show slots, ask for details
Intent: HIGH

User: "9 AM tomorrow works. My email is test@test.com"
Expected: Confirm and book, provide confirmation
Intent: HIGH
```

## 📝 Notes

1. **Session Management**: Currently in-memory. For production, use Redis or database.
2. **Mock Data**: Gym info uses mock data. Replace with real database queries.
3. **Calendly Fallback**: If Calendly API fails, mock slots are returned for testing.
4. **Rate Limiting**: Add rate limiting for production use.
5. **Authentication**: No auth implemented. Add for production.

## 🚀 Next Steps

1. Add conversation history persistence
2. Implement Redis for session management
3. Add analytics and tracking
4. Create Node.js version of Calendly service
5. Add webhook handlers for Calendly events
6. Implement A/B testing for different prompts

## 📚 API Reference

### POST /chat
Send a message to the agent

**Request:**
```json
{
  "message": "I want to book a trial",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "response": "Great! I can book your trial...",
  "session_id": "abc-123",
  "intent_level": "high",
  "booking_made": false
}
```

### POST /reset-session/{session_id}
Reset a conversation session

### GET /test-calendly
Test Calendly integration

### GET /health
Health check endpoint

---

**Built with:** FastAPI, LangChain, OpenAI GPT-4, Calendly API