"""
Main Kambo information agent
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResponse
from src.rag.knowledge_base import KnowledgeBase
from src.config import settings


class KamboAgent(BaseAgent):
    """Agent responsible for answering Kambo-related questions"""
    
    def __init__(self):
        super().__init__("Kambo Information Agent")
        self.knowledge_base = KnowledgeBase()
        
        # Define Kambo-related topics
        self.allowed_topics = [
            "kambo", "ceremony", "traditional", "amazonian", "medicine",
            "purification", "healing", "practitioner", "safety", "benefits",
            "research", "history", "preparation", "contraindications"
        ]
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Process user question about Kambo"""
        try:
            user_question = input_data.get("question", "")
            user_id = input_data.get("user_id", "anonymous")
            
            # Check if question is Kambo-related
            if not self._is_kambo_related(user_question):
                return AgentResponse(
                    success=False,
                    content="I can only answer questions related to Kambo ceremonies and traditional Amazonian medicine. Please ask about Kambo-related topics.",
                    metadata={"topic_check": "failed"}
                )
            
            # Get relevant information from knowledge base
            relevant_content = self.knowledge_base.get_relevant_content(user_question)
            
            # Generate response
            response = await self._generate_response(user_question, relevant_content)
            
            self.log_activity("Processed Kambo question", {
                "question_length": len(user_question),
                "user_id": user_id,
                "relevant_content_count": len(relevant_content)
            })
            
            return AgentResponse(
                success=True,
                content=response,
                metadata={
                    "relevant_content_count": len(relevant_content),
                    "topic_check": "passed",
                    "user_id": user_id
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "Processing Kambo question")
    
    def _is_kambo_related(self, question: str) -> bool:
        """Check if the question is related to Kambo"""
        question_lower = question.lower()
        return any(topic in question_lower for topic in self.allowed_topics)
    
    async def _generate_response(self, question: str, relevant_content: List[Dict[str, Any]]) -> str:
        """Generate response using relevant content"""
        if not relevant_content:
            return f"""I don't have specific information about that aspect of Kambo. 

{settings.medical_disclaimer}

For more detailed information, please consult with qualified Kambo practitioners or healthcare providers."""
        
        # Build response from relevant content
        context_parts = []
        for item in relevant_content:
            context_parts.append(item["content"])
        
        context = "\n\n".join(context_parts)
        
        response = f"""Based on available information about Kambo:

{context}

{settings.medical_disclaimer}

Please note that this information is for educational purposes only. Always consult with qualified healthcare providers and experienced Kambo practitioners before participating in any ceremonies."""
        
        return response 