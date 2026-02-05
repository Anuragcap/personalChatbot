import gradio as gr
from huggingface_hub import InferenceClient
import os
import time

pipe = None

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
    use_local_model,
    uploaded_file,
):
    start_time = time.time()

    file_context = extract_text_from_file(uploaded_file) if uploaded_file else ""
    enhanced_message = file_context + message if file_context else message

    messages = [{"role": "system", "content": system_message}]
    
    # Convert history to proper format
    for user_msg, bot_msg in history:
        messages.append({"role": "user", "content": user_msg})
        if bot_msg:
            messages.append({"role": "assistant", "content": bot_msg})
    
    messages.append({"role": "user", "content": enhanced_message})

    response = ""

    if use_local_model:
        print("[MODE] local")
        from transformers import pipeline
        global pipe
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
        
        # Get OAuth token from Gradio context
        request = gr.Request()
        hf_token = None
        
        try:
            if hasattr(request, 'username') and request.username:
                # User is logged in via OAuth
                from huggingface_hub import whoami
                hf_token = request.kwargs.get('token')
        except:
            pass
        
        if not hf_token:
            yield "⚠️ Please log in with your Hugging Face account first (click the login button at the top)."
            return

        try:
            client = InferenceClient(token=hf_token, model="meta-llama/Llama-3.2-3B-Instruct")

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
        except Exception as e:
            yield f"⚠️ Error with API: {str(e)}. Please make sure you're logged in with Hugging Face."


# Create the Gradio interface
with gr.Blocks(title="PersonalChatbot") as demo:
    gr.Markdown("<h1 style='text-align: center;'>for your second guesses</h1>")
    

    gr.LoginButton()
    
    chatbot = gr.Chatbot(label="Chat", height=500)
    
    with gr.Row():
        msg = gr.Textbox(
            label="Your Message",
            placeholder="Type your message here...",
            scale=4,
        )
        file_upload = gr.File(
            label="Upload File",
            file_types=[".txt", ".md", ".py", ".json", ".csv"],
            scale=1,
        )
    
    with gr.Row():
        submit_btn = gr.Button("Send", variant="primary")
        clear_btn = gr.ClearButton([msg, chatbot])
    
    with gr.Accordion("⚙️ Settings", open=False):
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
            label="Use Local Model (runs on Space hardware)",
            value=False,
        )
    
    # Event handlers
    msg.submit(
        respond,
        [msg, chatbot, system_message, max_tokens, temperature, top_p, use_local_model, file_upload],
        [chatbot],
    )
    
    submit_btn.click(
        respond,
        [msg, chatbot, system_message, max_tokens, temperature, top_p, use_local_model, file_upload],
        [chatbot],
    )

if __name__ == "__main__":
    demo.launch()
