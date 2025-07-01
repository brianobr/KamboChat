# Kambo Chatbot

A sophisticated AI chatbot for Kambo ceremony information using **LangGraph** for orchestration and medical verification.

## Features

- **LangGraph Architecture**: Advanced workflow orchestration with state management
- **Medical Verification**: AI-powered medical advice validation with feedback loop
- **Content Moderation**: Policy violation detection and filtering
- **Safety Checking**: Comprehensive safety validation for all requests
- **Retry Mechanism**: Up to 3 attempts with enhanced prompts for medical content
- **Real-time Streaming**: Live response streaming via Gradio interface
- **Database Logging**: Complete conversation and security event logging
- **Azure Integration**: Key Vault integration for secure secret management

## Architecture

The chatbot uses a sophisticated LangGraph flow:

```
Input Validation → Content Moderation → Safety Check → Context Retrieval → 
Response Generation → Medical Verification → [Retry Loop] → Final Response
```

### Key Components

- **Input Validation**: Sanitizes and validates user input
- **Content Moderation**: Checks for policy violations
- **Safety Checking**: Ensures requests are appropriate
- **Medical Verification**: Validates medical advice with feedback
- **Retry Mechanism**: Up to 3 attempts with enhanced prompts
- **Error Handling**: Comprehensive error management

## Quick Start

### Prerequisites

- Python 3.12+
- OpenAI API key
- Azure Key Vault (optional, for production)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd kambo_chatbot

# Install dependencies
uv sync

# Set environment variables
export OPENAI_API_KEY=your_openai_api_key
```

### Running the Application

```bash
# Start the API server
python main.py

# In another terminal, start the Gradio interface
python gradio_app.py
```

### Testing

```bash
# Run all tests
python test_graph.py
```

## API Usage

### Health Check
```bash
curl http://localhost:8000/health
```

### Chat Endpoint
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is a Kambo ceremony?",
    "user_id": "test_user"
  }'
```

### Graph Info
```bash
curl http://localhost:8000/graph-info
```

## Web Interface

- **API Documentation**: http://localhost:8000/docs
- **Gradio Interface**: http://localhost:8090

## Production Deployment

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_api_key
AZURE_KEY_VAULT_URL=your_key_vault_url  # Optional
AZURE_TENANT_ID=your_tenant_id          # Optional
AZURE_CLIENT_ID=your_client_id          # Optional
```

### Docker
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
EXPOSE 8000 8090
CMD ["python", "main.py"]
```

### Azure App Service
1. Deploy `main.py` as your main app
2. Configure environment variables
3. Use Azure Key Vault for secret management

## Medical Verification

The system includes advanced medical verification:

1. **Initial Response**: Generate Kambo-specific response
2. **Medical Check**: Verify medical advice for safety
3. **Feedback Loop**: If issues found, retry with enhanced prompts
4. **Final Response**: Deliver safe, verified information

## Security Features

- Input validation and sanitization
- Content moderation for policy violations
- Comprehensive error handling
- Security event logging
- Azure Key Vault integration

## Performance

- **Response Time**: 5-15 seconds for complex queries
- **Safety**: Highest level of medical verification
- **Scalability**: LangGraph provides excellent scalability
- **Reliability**: Retry mechanism ensures robust responses

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Disclaimer

This chatbot provides educational information about Kambo ceremonies and traditional Amazonian medicine. It is not intended as medical advice. Always consult with qualified healthcare providers before making any health-related decisions. 