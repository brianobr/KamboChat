"""
Gradio interface for the Kambo chatbot with streaming capabilities
"""

import asyncio
import gradio as gr
from loguru import logger
import sys
import os
import uuid

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.langchain.coordinator import Coordinator
from src.config import settings
from src.database.connection import init_database


class StreamingCoordinator(Coordinator):
    """Coordinator with streaming capabilities for Gradio"""
    
    async def process_message_stream(self, user_message: str, user_id: str = None):
        logger.info(f"[Gradio] process_message_stream called with user_message='{user_message}', user_id='{user_id}'")
        conversation_id = str(uuid.uuid4())
        user_id = user_id or "anonymous"
        
        try:
            conversation_history = self._load_conversation_history(user_id)
            logger.info(f"[Gradio] Loaded conversation history: {conversation_history}")
            initial_state = {
                "messages": [],
                "user_message": user_message,
                "user_id": user_id,
                "conversation_id": conversation_id,
                "conversation_history": conversation_history,
                "validation_result": None,
                "moderation_result": None,
                "safety_check_result": None,
                "rag_context": None,
                "kambo_response": None,
                "medical_verification_result": None,
                "medical_verification_attempts": 0,
                "medical_verification_feedback": [],
                "final_response": None,
                "error": None,
                "metadata": None
            }
            logger.info("[Gradio] Awaiting self.graph.ainvoke(initial_state)")
            result = await self.graph.ainvoke(initial_state)
            logger.info(f"[Gradio] LangGraph result: {result}")
            final_response = result.get("final_response", "I apologize, but I encountered an error processing your request.")
            error = result.get("error")
            if error:
                logger.error(f"[Gradio] Error in result: {error}")
                yield "I'm sorry, but I cannot process that request. Please rephrase your question."
            else:
                words = final_response.split()
                partial_response = ""
                for i, word in enumerate(words):
                    partial_response += word + " "
                    yield partial_response.strip()
                    await asyncio.sleep(0.05)
                asyncio.create_task(self._save_conversation_async(
                    conversation_id, 
                    user_id, 
                    user_message, 
                    final_response
                ))
        except Exception as e:
            logger.error(f"[Gradio] Exception in process_message_stream: {e}")
            yield "I apologize, but I encountered an error processing your request. Please try again."


# Initialize the streaming coordinator
streaming_coordinator = StreamingCoordinator()


async def chat_with_kambo(message, history):
    logger.info(f"[Gradio] chat_with_kambo called with message='{message}' and history={history}")
    if not message.strip():
        logger.info("[Gradio] Empty message, returning early.")
        yield "", history
        return

    # Add user message in messages format
    history.append({"role": "user", "content": message})

    # If last message is not assistant, append a new assistant message
    if not history or history[-1]["role"] != "assistant":
        history.append({"role": "assistant", "content": ""})

    try:
        logger.info("[Gradio] Entering async for chunk in process_message_stream...")
        async for chunk in streaming_coordinator.process_message_stream(message):
            logger.info(f"[Gradio] Yielding chunk: {chunk}")
            history[-1]["content"] = chunk
            yield "", history
        logger.info("[Gradio] Finished streaming response.")
    except Exception as e:
        logger.error(f"[Gradio] Exception in chat_with_kambo: {e}")
        yield "Sorry, there was an error processing your request.", history


def create_gradio_interface():
    """Create the Gradio interface"""
    
    # Custom CSS for better styling
    css = """
    .gradio-container {
        max-width: 800px;
        margin: 0 auto;
    }
    .chat-message {
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
    }
    .user-message {
        background-color: #e3f2fd;
        text-align: right;
    }
    .bot-message {
        background-color: #f5f5f5;
        text-align: left;
    }
    """
    
    with gr.Blocks(css=css, title="Kambo Chatbot", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🐸 Kambo Chatbot
        
        Welcome to the Kambo information assistant! I can help you learn about:
        
        - Traditional Kambo ceremonies and practices
        - Cultural and historical context
        - Safety considerations and research
        - Matt O'Brien's experience and training
        
        **Note:** This information is for educational purposes only. Always consult with qualified healthcare providers for medical advice.
        """)
        
        chatbot = gr.Chatbot(
            height=500,
            show_label=False,
            container=True,
            bubble_full_width=False,
            avatar_images=["👤", "🐸"],
            type="messages"
        )
        
        with gr.Row():
            with gr.Column(scale=4):
                msg = gr.Textbox(
                    placeholder="Ask me about Kambo ceremonies, traditional practices, or Matt O'Brien's experience...",
                    show_label=False,
                    container=False
                )
            
            with gr.Column(scale=1):
                submit_btn = gr.Button("Send", variant="primary")
                clear_btn = gr.Button("Clear", variant="secondary")
        
        # Event handlers
        msg.submit(
            chat_with_kambo,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot],
            show_progress=True
        )
        
        submit_btn.click(
            chat_with_kambo,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot],
            show_progress=True
        )
        
        clear_btn.click(lambda: ([], ""), outputs=[chatbot, msg])
        
        gr.Markdown("""
        ---
        **Disclaimer:** This chatbot provides educational information about Kambo ceremonies and traditional Amazonian medicine. 
        It is not intended as medical advice. Always consult with qualified healthcare providers for medical advice.
        """)
    
    return demo 