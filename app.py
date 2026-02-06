import gradio as gr
from huggingface_hub import InferenceClient
import os
import time

def extract_text_from_file(file):
    """Extract text content from uploaded file"""
    if file is None:
        return ""
    
    try:
        file_path = file.name if hasattr(file, 'name') else file
        
        if file_path.endswith(('.txt', '.md', '.py', '.json', '.csv')):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return f"\n\n[Context from file: {os.path.basename(file_path)}]\n{content}\n[End of file context]\n"
        else:
            return f"\n\n[File uploaded: {os.path.basename(file_path)}]\n"
    
    except Exception as e:
        return f"\n\n[Error reading file: {str(e)}]\n"


def respond(message, history, request: gr.Request):
    """Simple chatbot response function"""
    start_time = time.time()
    
    # Get OAuth token from request
    token = None
    if request:
        try:
            token = request.headers.get("authorization", "").replace("Bearer ", "")
            if not token and hasattr(request, "username"):
                # Try to get from OAuth
                token = request.oauth_token if hasattr(request, "oauth_token") else None
        except:
            pass
    
    # Fallback to environment variable
    if not token:
        token = os.getenv("HF_TOKEN")
    
    if not token:
        yield "⚠️ Please log in with Hugging Face to use this chatbot. Click the 'Sign in with Hugging Face' button above."
        return
    
    # Build messages for API
    messages = [{"role": "system", "content": "You are a friendly and helpful AI assistant."}]
    
    # Add history
    for user_msg, bot_msg in history:
        messages.append({"role": "user", "content": user_msg})
        if bot_msg:
            messages.append({"role": "assistant", "content": bot_msg})
    
    # Add current message
    messages.append({"role": "user", "content": message})
    
    # Use InferenceClient for API response
    try:
        client = InferenceClient(model="meta-llama/Llama-3.2-3B-Instruct", token=token)
        
        response = ""
        for chunk in client.chat_completion(
            messages,
            max_tokens=512,
            stream=True,
            temperature=0.7,
        ):
            if chunk.choices and chunk.choices[0].delta.content:
                response += chunk.choices[0].delta.content
                yield response
        
        # Add response time
        end_time = time.time()
        response_time = end_time - start_time
        yield f"{response}\n\n⏱️ *Response time: {response_time:.2f}s*"
        
    except Exception as e:
        yield f"Error: {str(e)}\n\nPlease try logging in with Hugging Face or check your connection."


# Create the Gradio interface using ChatInterface
demo = gr.ChatInterface(
    fn=respond,
    title="🌟 Enhanced AI Chatbot 🌟",
    description="""
    ### Features:
    - 💬 Chat with AI assistant
    - ⏱️ Response time tracking
    - 🚀 Powered by Llama 3.2 3B
    
    **Note:** You need to sign in with Hugging Face to use this chatbot.
    """,
    examples=[
        "What is machine learning?",
        "Explain Python decorators",
        "Write a haiku about coding",
    ],
    cache_examples=False,
)

if __name__ == "__main__":
    demo.launch()