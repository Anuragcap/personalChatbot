import gradio as gr
from huggingface_hub import InferenceClient
import os
import time
from datetime import datetime

pipe = None
stop_inference = False

# Fancy styling
fancy_css = """
#main-container {
    background-color: #f0f0f0;
    font-family: 'Arial', sans-serif;
}
.gradio-container {
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
    background: white;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    border-radius: 10px;
}
.gr-button {
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 10px 20px;
    cursor: pointer;
    transition: background-color 0.3s ease;
}
.gr-button:hover {
    background-color: #45a049;
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
            return f"\n\n[File uploaded: {os.path.basename(file_path)} - content extraction not supported for this file type]\n"
    
    except Exception as e:
        return f"\n\n[Error reading file: {str(e)}]\n"


def respond(
    message,
    history: list[dict[str, str]],
    system_message,
    max_tokens,
    temperature,
    top_p,
    hf_token: gr.OAuthToken,
    use_local_model: bool,
    uploaded_file,
):
    global pipe
    
    start_time = time.time()

    file_context = extract_text_from_file(uploaded_file) if uploaded_file else ""
    enhanced_message = file_context + message if file_context else message

    messages = [{"role": "system", "content": system_message}]
    messages.extend(history)
    messages.append({"role": "user", "content": enhanced_message})

    response = ""

    if use_local_model:
        print("[MODE] local")
        from transformers import pipeline
        import torch
        if pipe is None:
            pipe = pipeline("text-generation", model="microsoft/Phi-3-mini-4k-instruct")

        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])

        outputs = pipe(
            prompt,
            max_new_tokens=max_tokens,
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
        )

        response = outputs[0]["generated_text"][len(prompt):]
        end_time = time.time()
        response_time = end_time - start_time
        
        response_with_time = f"{response.strip()}\n\n⏱️ *Response time: {response_time:.2f}s (Local Model)*"
        yield response_with_time

    else:
        print("[MODE] api")

        if hf_token is None or not getattr(hf_token, "token", None):
            yield "⚠️ Please log in with your Hugging Face account first."
            return

        client = InferenceClient(token=hf_token.token, model="meta-llama/Llama-3.2-3B-Instruct")

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
        
        end_time = time.time()
        response_time = end_time - start_time
        
        response_with_time = f"{response}\n\n⏱️ *Response time: {response_time:.2f}s (API Model)*"
        yield response_with_time


with gr.Blocks(css=fancy_css) as demo:
    with gr.Row():
        gr.Markdown("<h1 style='text-align: center;'>🌟 Enhanced AI Chatbot 🌟</h1>")
        gr.LoginButton()
    
    gr.Markdown("""
    ### Features:
    - 📁 Upload files (.txt, .md, .py, .json, .csv) to provide context
    - ⏱️ Response time tracking for performance comparison
    - 🤖 Choose between API and Local model execution
    """)
    
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                label="Chat",
                type="messages",
                height=500,
            )
            
            with gr.Row():
                msg = gr.Textbox(
                    label="Your Message",
                    placeholder="Type your message here...",
                    scale=4,
                )
                file_upload = gr.File(
                    label="Upload Context File (optional)",
                    file_types=[".txt", ".md", ".py", ".json", ".csv"],
                    scale=1,
                )
            
            with gr.Row():
                submit_btn = gr.Button("Send", variant="primary")
                clear_btn = gr.ClearButton([msg, chatbot])
        
        with gr.Column(scale=1):
            gr.Markdown("### ⚙️ Settings")
            
            system_message = gr.Textbox(
                value="You are a friendly and helpful AI assistant.",
                label="System Message",
                lines=3,
            )
            
            max_tokens = gr.Slider(
                minimum=1,
                maximum=2048,
                value=512,
                step=1,
                label="Max New Tokens",
            )
            
            temperature = gr.Slider(
                minimum=0.1,
                maximum=2.0,
                value=0.7,
                step=0.1,
                label="Temperature",
            )
            
            top_p = gr.Slider(
                minimum=0.1,
                maximum=1.0,
                value=0.95,
                step=0.05,
                label="Top-p",
            )
            
            use_local_model = gr.Checkbox(
                label="Use Local Model",
                value=False,
            )
    
    def user_submit(message, history, file):
        if not message.strip():
            return "", history, file
        return "", history + [{"role": "user", "content": message}], file
    
    def bot_response(history, system_msg, max_tok, temp, top_p_val, hf_token, use_local, file):
        if not history:
            return history
        
        user_message = history[-1]["content"]
        
        generator = respond(
            message=user_message,
            history=history[:-1],
            system_message=system_msg,
            max_tokens=max_tok,
            temperature=temp,
            top_p=top_p_val,
            hf_token=hf_token,
            use_local_model=use_local,
            uploaded_file=file,
        )
        
        for response_text in generator:
            history[-1] = {"role": "user", "content": user_message}
            yield history + [{"role": "assistant", "content": response_text}]
    
    msg.submit(
        user_submit,
        [msg, chatbot, file_upload],
        [msg, chatbot, file_upload],
        queue=False,
    ).then(
        bot_response,
        [chatbot, system_message, max_tokens, temperature, top_p, gr.State(), use_local_model, file_upload],
        chatbot,
    )
    
    submit_btn.click(
        user_submit,
        [msg, chatbot, file_upload],
        [msg, chatbot, file_upload],
        queue=False,
    ).then(
        bot_response,
        [chatbot, system_message, max_tokens, temperature, top_p, gr.State(), use_local_model, file_upload],
        chatbot,
    )

if __name__ == "__main__":
    demo.launch()
