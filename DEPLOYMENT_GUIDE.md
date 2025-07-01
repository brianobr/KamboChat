# Kambo Chatbot Deployment Guide

## Overview

This guide covers deployment and usage instructions for the Kambo chatbot using LangGraph.

## Architecture

The Kambo chatbot uses **LangGraph** for orchestration with the following features:

- **Input Validation**: Sanitizes and validates user input
- **Content Moderation**: Checks for policy violations
- **Safety Checking**: Ensures requests are appropriate
- **Context Retrieval**: Gathers relevant information
- **Response Generation**: Creates Kambo-specific responses
- **Medical Verification**: Validates medical advice with feedback loop
- **Retry Mechanism**: Up to 3 attempts with enhanced prompts
- **Error Handling**: Comprehensive error management

## Quick Start

### Local Development

```bash
# Install dependencies
uv sync

# Start the API server
python main.py

# In another terminal, start the Gradio interface
python gradio_app.py
```

### Production Deployment

```bash
# Start the production server
python main.py
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

## Gradio Interface

The web interface is available at:
- **API**: http://localhost:8000
- **Gradio**: http://localhost:8090

## Testing

### Run All Tests
```bash
python test_graph.py
```

### Test Medical Verification Loop
The system automatically tests medical verification with retry logic.

## Production Deployment

### Environment Variables
```bash
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional (for Azure Key Vault)
AZURE_KEY_VAULT_URL=your_key_vault_url
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
```

### Docker Deployment
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install uv
RUN uv sync

EXPOSE 8000 8090

CMD ["python", "main.py"]
```

### Azure App Service
1. Deploy `main.py` as your main app
2. Set environment variables in Azure App Service Configuration
3. Use Azure Key Vault for secret management

### Local Development
```bash
# Install development dependencies
uv sync --dev

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run Gradio with auto-reload
python gradio_app.py
```

## LangGraph Flow

The chatbot uses a sophisticated LangGraph flow:

```
Input Validation → Content Moderation → Safety Check → Context Retrieval → 
Response Generation → Medical Verification → [Retry Loop] → Final Response
```

### Key Features

| Feature | Description |
|---------|-------------|
| Input Validation | Sanitizes and validates user input |
| Content Moderation | Checks for policy violations |
| Safety Checking | Ensures requests are appropriate |
| Medical Verification | Validates medical advice with feedback |
| Retry Mechanism | Up to 3 attempts with enhanced prompts |
| Error Handling | Comprehensive error management |
| Streaming | Real-time response streaming |
| Database Logging | Conversation and security logging |

## Troubleshooting

### Common Issues

1. **LangGraph not found**
   ```bash
   uv add langgraph
   ```

2. **OpenAI API key not found**
   - Set `OPENAI_API_KEY` environment variable
   - Or configure Azure Key Vault

3. **Database connection issues**
   ```bash
   # Initialize database
   python -c "from src.database.connection import init_database; init_database()"
   ```

4. **Port already in use**
   ```bash
   # Change ports in the main files
   # API: port=8001
   # Gradio: server_port=8091
   ```

### Logs
The system uses structured logging with loguru. Check logs for:
- Input validation results
- Medical verification feedback
- Retry attempts
- Error details

## Performance Considerations

- **Response Time**: 5-15 seconds for complex queries with retries
- **Cost**: Higher due to multiple LLM calls for verification
- **Safety**: Highest level of safety and compliance
- **Scalability**: LangGraph provides excellent scalability

## Next Steps

1. **Deploy to production** using your preferred method
2. **Monitor performance** and adjust as needed
3. **Iterate on prompts** based on user feedback
4. **Add custom features** as required

## Support

For issues or questions:
1. Check the test files for examples
2. Review the logs for detailed error information
3. Test with different input types to understand behavior 