import gradio as gr
import requests
import os
import time


BACKEND_URL = os.environ.get("BACKEND_URL", "http://paffenroth-23.dyn.wpi.edu:9008")

fancy_css = """
#main-container { background-color: #1a1a1a; font-family: 'Arial', sans-serif; min-height: 100vh; }
.gradio-container { max-width: 700px; margin: 0 auto; padding: 20px;
    background: #00CED1; box-shadow: 0 8px 32px rgba(0,147,233,0.2); border-radius: 15px; }
.gr-button { background: linear-gradient(135deg,#0093E9 0%,#80D0C7 100%);
    color: white; border: none; border-radius: 5px; padding: 10px 20px;
    cursor: pointer; transition: all 0.3s ease; }
"""

def chat_via_api(
    message,
    history,
    system_message,
    max_tokens,
    temperature,
    top_p,
    hf_token,
    use_local_model,
):
   
    if not message.strip():
        yield "Please enter a message."
        return

    # Convert Gradio history format to API format
    formatted_history = []
    if history:
        for item in history:
            if isinstance(item, dict):
                formatted_history.append({"role": item["role"], "content": item["content"]})
            else:
                user_msg, bot_msg = item
                formatted_history.append({"role": "user", "content": user_msg})
                if bot_msg:
                    formatted_history.append({"role": "assistant", "content": bot_msg})

    payload = {
        "message": message,
        "history": formatted_history,
        "system_message": system_message,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "hf_token": hf_token if hf_token else None,
        "use_local_model": use_local_model,
    }

    yield " Waiting for response from backend..."

    try:
        resp = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=120)
        if resp.status_code == 200:
            data = resp.json()
            response = data["response"]
            response_time = data["response_time"]
            model = data["model_used"]
            yield f"{response}\n\n⏱️ *Response time: {response_time}s | Model: {model}*"
        elif resp.status_code == 401:
            yield "Authentication error: Please provide a valid HF token."
        else:
            yield f"Backend error {resp.status_code}: {resp.text}"
    except requests.exceptions.ConnectionError:
        yield f"Cannot connect to backend at {BACKEND_URL}. Is it running?"
    except requests.exceptions.Timeout:
        yield "Request timed out. The model may be loading — try again."
    except Exception as e:
        yield f"Unexpected error: {str(e)}"




chatbot = gr.ChatInterface(
    fn=chat_via_api,
    additional_inputs=[
        gr.Textbox(value="You are a Coding Expert.", label="System message"),
        gr.Slider(minimum=1, maximum=2048, value=512, step=1, label="Max new tokens"),
        gr.Slider(minimum=0.1, maximum=2.0, value=0.7, step=0.1, label="Temperature"),
        gr.Slider(minimum=0.1, maximum=1.0, value=0.95, step=0.05, label="Top-p"),
        gr.Textbox(label="HF Token (for API mode)", type="password", placeholder="hf_..."),
        gr.Checkbox(label="Use Local Model (slower, no token needed)", value=False),
    ],
)

with gr.Blocks(css=fancy_css) as demo:
    gr.Markdown("<h1 style='text-align:center;'>🤖 Personal Code Assistant — Group 8</h1>")
    gr.Markdown(f"<p style='text-align:center;color:gray;'>Backend: <code>{BACKEND_URL}</code></p>")
    chatbot.render()

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7008)