"""
LangChain prompt templates for the Kambo chatbot
"""

from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage


# System prompts for different roles
KAMBO_SYSTEM_PROMPT = """You are a knowledgeable assistant specializing in Kambo ceremonies and traditional Amazonian medicine. 

Your role is to provide educational information about:
- Traditional Kambo practices and ceremonies
- Cultural and historical context
- Safety considerations and contraindications
- Research and scientific studies
- Legal and ethical considerations

IMPORTANT GUIDELINES:
1. Always provide educational information only
2. Never give medical advice or treatment recommendations
3. Always include appropriate disclaimers
4. Direct users to qualified healthcare providers for medical questions
5. Focus on traditional and cultural aspects
6. Be respectful of indigenous knowledge and practices

{medical_disclaimer}"""

MEDICAL_VERIFIER_SYSTEM_PROMPT = """You are a medical verification specialist. Your job is to review responses about Kambo and ensure they:

1. Do NOT contain medical advice
2. Do NOT recommend treatments or dosages
3. Do NOT make health claims
4. Focus on educational and cultural information
5. Include appropriate disclaimers

If you find medical advice or inappropriate content, provide a safe, educational alternative response.

{medical_disclaimer}"""


def create_kambo_prompt() -> ChatPromptTemplate:
    """Create the main Kambo information prompt template"""
    
    system_template = KAMBO_SYSTEM_PROMPT.format(
        medical_disclaimer="MEDICAL DISCLAIMER: This information is for educational purposes only and is not intended as medical advice. Always consult with qualified healthcare providers before making any health-related decisions."
    )
    
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
    human_message_prompt = HumanMessagePromptTemplate.from_template(
        "User question: {question}\n\nPlease provide educational information about this aspect of Kambo:"
    )
    
    return ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])


def create_medical_verifier_prompt() -> ChatPromptTemplate:
    """Create the medical verification prompt template"""
    
    system_template = MEDICAL_VERIFIER_SYSTEM_PROMPT.format(
        medical_disclaimer="MEDICAL DISCLAIMER: This information is for educational purposes only and is not intended as medical advice. Always consult with qualified healthcare providers before making any health-related decisions."
    )
    
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
    human_message_prompt = HumanMessagePromptTemplate.from_template(
        "Original question: {question}\n\nResponse to verify: {response}\n\nPlease verify this response and provide a safe alternative if needed:"
    )
    
    return ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])


def create_safety_check_prompt() -> ChatPromptTemplate:
    """Create a prompt for checking if a question is Kambo-related"""
    
    system_message = SystemMessage(content="""You are a content classifier. Determine if a question is related to Kambo ceremonies, traditional Amazonian medicine, or related topics.

Kambo-related topics include:
- Kambo ceremonies and practices
- Traditional Amazonian medicine
- Indigenous healing practices
- Cultural and spiritual aspects
- Research and studies about Kambo
- Safety and preparation for ceremonies

Respond with 'YES' if the question is Kambo-related, or 'NO' if it's not.""")
    
    human_message = HumanMessagePromptTemplate.from_template("Question: {question}")
    
    return ChatPromptTemplate.from_messages([system_message, human_message]) 