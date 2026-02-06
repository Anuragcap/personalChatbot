import gradio as gr
from huggingface_hub import InferenceClient
import os
import time

pipe = None
stop_inference = False


fancy_css = """
#main-container {
    background-color: #1a1a1a;  /* Dark teal */
    font-family: 'Arial', sans-serif;
    min-height: 100vh;
}
.gradio-container {
    max-width: 700px;
    margin: 0 auto;
    padding: 20px;
    background: #0093E9
    box-shadow: 0 8px 32px rgba(0, 147, 233, 0.2);
    border-radius: 15px;
}
.gr-button {
    background: linear-gradient(135deg, #0093E9 0%, #80D0C7 100%);
    color: white;
    border: none;
    border-radius: 5px;
    padding: 10px 20px;
    cursor: pointer;
    transition: all 0.3s ease;
}
.gr-button:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(0, 147, 233, 0.3);
}
.gr-slider input {
    color: #0093E9;
}
.gr-chat {
    font-size: 16px;
}
#title {
    text-align: center;
    font-size: 2em;
    margin-bottom: 20px;
    color: #333;
}
"""

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


def respond(
    message,
    history,
    system_message,
    max_tokens,
    temperature,
    top_p,
    file_upload,
    hf_token: gr.OAuthToken,
    use_local_model: bool,
):
    global pipe
    start_time = time.time()
    
    # Extract file context if provided
    file_context = extract_text_from_file(file_upload)
    
    # Build messages for API
    messages = [{"role": "system", "content": system_message}]
    
    # Add history - handle both list of dicts and list of tuples
    if history:
        # Check if history is a list of dicts (new format) or list of tuples (old format)
        if isinstance(history[0], dict):
            # New format: list of dicts with 'role' and 'content'
            for msg in history:
                messages.append(msg)
        else:
            # Old format: list of tuples [(user_msg, bot_msg), ...]
            for user_msg, bot_msg in history:
                messages.append({"role": "user", "content": user_msg})
                if bot_msg:
                    messages.append({"role": "assistant", "content": bot_msg})
    
    # Add current message with file context
    full_message = file_context + message if file_context else message
    messages.append({"role": "user", "content": full_message})
    
    response = ""
    
    if use_local_model:
        print("[MODE] local")
        from transformers import pipeline
        import torch
        if pipe is None:
            pipe = pipeline("text-generation", model="microsoft/Phi-3-mini-4k-instruct")
        
        # Build prompt as plain text
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
        outputs = pipe(
            prompt,
            max_new_tokens=max_tokens,
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
        )
        
        response = outputs[0]["generated_text"][len(prompt):]
        
        # Add response time
        end_time = time.time()
        response_time = end_time - start_time
        yield f"{response.strip()}\n\n⏱️ *Response time: {response_time:.2f}s*"
    
    else:
        print("[MODE] api")
        
        if hf_token is None or not getattr(hf_token, "token", None):
            yield "⚠️ Please log in with your Hugging Face account first."
            return
        
        client = InferenceClient(token=hf_token.token, model="meta-llama/Llama-3.2-3B-Instruct")
        
        try:
            for chunk in client.chat_completion(
                messages,
                max_tokens=max_tokens,
                stream=True,
                temperature=temperature,
                top_p=top_p,
            ):
                choices = chunk.choices
                token = ""
                if len(choices) and choices[0].delta.content:
                    token = choices[0].delta.content
                response += token
                yield response
            
            # Add response time
            end_time = time.time()
            response_time = end_time - start_time
            yield f"{response}\n\n⏱️ *Response time: {response_time:.2f}s*"
        except Exception as e:
            yield f"Error: {str(e)}\n\nPlease try again."


chatbot = gr.ChatInterface(
    fn=respond,
    additional_inputs=[
        gr.Textbox(value="You are a friendly Chatbot.", label="System message"),
        gr.Slider(minimum=1, maximum=2048, value=512, step=1, label="Max new tokens"),
        gr.Slider(minimum=0.1, maximum=2.0, value=0.7, step=0.1, label="Temperature"),
        gr.Slider(minimum=0.1, maximum=1.0, value=0.95, step=0.05, label="Top-p (nucleus sampling)"),
        gr.File(
            label="📁 Upload file for context (optional)",
            file_types=[".txt", ".md", ".py", ".json", ".csv"]
        ),
        gr.Checkbox(label="Use Local Model", value=False),
    ],
)

with gr.Blocks() as demo:
    with gr.Row():
        gr.Markdown("<h1 style='text-align: center;'>🌟 Fancy AI Chatbot 🌟</h1>")
        gr.LoginButton()
    
    
    
    chatbot.render()

if __name__ == "__main__":
    demo.launch(css=fancy_css)