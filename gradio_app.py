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
        """Process a user message with streaming response"""
        conversation_id = str(uuid.uuid4())
        
        try:
            # Execute the graph
            result = await self.graph.ainvoke({
                "user_message": user_message,
                "user_id": user_id or "anonymous"
            })
            
            # Handle different routing outcomes
            if result["routing"]["route"] == "error":
                yield "I'm sorry, but I cannot process that request. Please rephrase your question."
                return
            
            elif result["final_routing"]["route"] == "success":
                response = result["final_routing"]["response"]
                
                # Stream the response word by word
                words = response.split()
                partial_response = ""
                
                for i, word in enumerate(words):
                    partial_response += word + " "
                    yield partial_response.strip()
                    
                    # Small delay for streaming effect
                    await asyncio.sleep(0.05)
                
                # Save to database asynchronously
                asyncio.create_task(self._save_conversation_async(
                    conversation_id, 
                    result["final_routing"]["user_id"], 
                    user_message, 
                    response
                ))
                
            else:
                yield "I apologize, but I encountered an unexpected error. Please try again."
                
        except Exception as e:
            logger.error(f"Error in streaming coordinator: {e}")
            yield "I apologize, but I encountered an error processing your request. Please try again."


# Initialize the streaming coordinator
streaming_coordinator = StreamingCoordinator()


def chat_with_kambo(message, history):
    """Chat function for Gradio interface"""
    if not message.strip():
        return "", history
    
    # Add user message to history
    history.append([message, ""])
    
    # Process the message with streaming
    async def get_response():
        async for chunk in streaming_coordinator.process_message_stream(message):
            history[-1][1] = chunk
            yield history
    
    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        for updated_history in loop.run_until_complete(get_response()):
            yield updated_history
    finally:
        loop.close()


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
            avatar_images=["👤", "🐸"]
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
        It is not intended as medical advice. Always consult with qualified healthcare providers before making any health-related decisions.
        """)
    
    return demo


if __name__ == "__main__":
    # Initialize database
    init_database()
    
    # Create and launch the Gradio interface
    demo = create_gradio_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True
    ) 