# Kambo Chatbot

A multi-agent chatbot system for providing information about Kambo ceremonies and traditional practices.

## Features

- **Multi-Agent Architecture**: Specialized agents for different tasks
- **RAG System**: Knowledge base for accurate information retrieval
- **Medical Verification**: Ensures responses don't contain medical advice
- **Security**: Input validation and prompt injection protection
- **Compliance**: Built-in medical disclaimers and safety measures
- **Database**: Conversation logging and security event tracking

## Architecture

### Agents
1. **Kambo Agent**: Main agent for answering Kambo-related questions
2. **Medical Verifier**: Ensures responses don't contain medical advice
3. **Security Validator**: Protects against malicious inputs

### Components
- **Knowledge Base**: Manages RAG data sources
- **Input Validator**: Security and input validation
- **Coordinator**: Orchestrates all agents
- **Database**: SQLAlchemy models for data persistence

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
```bash
cp .env.example .env
# Edit .env with your actual values
```

3. Run the application:
```bash
python main.py
```

4. Access the API:
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## API Usage

### Chat Endpoint
```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "What is Kambo?", "user_id": "user123"}'
```

## Development

- Follow the coding standards in `.cursor/cursor.json`
- Write tests for all new functionality
- Maintain security best practices
- Always include medical disclaimers

## Safety & Compliance

- All responses include medical disclaimers
- No medical advice is provided
- Users are directed to qualified healthcare providers
- Input validation prevents malicious content
- Comprehensive logging for audit trails

## Next Steps

1. **Add OpenAI Integration**: Implement actual LLM responses
2. **Enhance RAG**: Add vector search and document processing
3. **Add Authentication**: User management system
4. **Deploy**: Choose hosting platform (Azure, Vercel, etc.)
5. **Monitoring**: Add analytics and monitoring 