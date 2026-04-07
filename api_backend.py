from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List, Dict
import time
import os
from dotenv import load_dotenv
from prometheus_client import (
    Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
)

load_dotenv()

# --- Prometheus Metrics ---
chat_requests_total = Counter(
    "chatbot_requests_total",
    "Total number of chat requests",
    ["status", "model_type"],  # status: success|error, model_type: api|local
)
chat_errors_total = Counter(
    "chatbot_errors_total",
    "Total number of chat errors by type",
    ["error_type"],  # auth_error | hf_api_error | local_model_error
)
chat_response_time_seconds = Histogram(
    "chatbot_response_time_seconds",
    "Time taken to generate a chat response",
    buckets=[0.5, 1, 2, 5, 10, 30, 60, 120],
)
chat_active_requests = Gauge(
    "chatbot_active_requests",
    "Number of chat requests currently being processed",
)
chat_tokens_requested = Histogram(
    "chatbot_tokens_requested",
    "Distribution of max_tokens requested per chat",
    buckets=[64, 128, 256, 512, 1024, 2048],
)
chat_history_length = Histogram(
    "chatbot_history_length",
    "Number of prior messages in history per request",
    buckets=[0, 1, 2, 5, 10, 20, 50],
)
# --------------------------

app = FastAPI(
    title="Group 8 Personal Chatbot API",
    description="Backend API for the CS553 Personal Chatbot (Case Study 2)",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_ID = "Qwen/QwQ-32B"


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    system_message: Optional[str] = "You are a Coding Expert."
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.95
    hf_token: Optional[str] = None
    use_local_model: Optional[bool] = False


class ChatResponse(BaseModel):
    response: str
    response_time: float
    model_used: str


class HealthResponse(BaseModel):
    status: str
    backend_port: int
    timestamp: float


@app.get("/", response_model=HealthResponse)
def root():
    """Health check endpoint."""
    return HealthResponse(status="ok", backend_port=9008, timestamp=time.time())


@app.get("/health", response_model=HealthResponse)
def health():
    """Health check for automated monitoring."""
    return HealthResponse(status="ok", backend_port=9008, timestamp=time.time())


@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    chat_active_requests.inc()
    chat_tokens_requested.observe(request.max_tokens)
    chat_history_length.observe(len(request.history))

    start_time = time.time()
    model_type = "local" if request.use_local_model else "api"

    messages = [{"role": "system", "content": request.system_message}]
    for msg in request.history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": request.message})

    response_text = ""
    model_used = ""

    try:
        if request.use_local_model:
            try:
                from transformers import pipeline

                model_used = "microsoft/Phi-3-mini-4k-instruct (local)"
                pipe = pipeline("text-generation", model="microsoft/Phi-3-mini-4k-instruct")
                prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                outputs = pipe(
                    prompt,
                    max_new_tokens=request.max_tokens,
                    do_sample=True,
                    temperature=request.temperature,
                    top_p=request.top_p,
                )
                response_text = outputs[0]["generated_text"][len(prompt) :].strip()
            except Exception as e:
                chat_errors_total.labels(error_type="local_model_error").inc()
                chat_requests_total.labels(status="error", model_type=model_type).inc()
                raise HTTPException(status_code=500, detail=f"Local model error: {str(e)}")

        else:
            hf_token = request.hf_token or os.environ.get("HF_TOKEN")
            if not hf_token:
                chat_errors_total.labels(error_type="auth_error").inc()
                chat_requests_total.labels(status="error", model_type=model_type).inc()
                raise HTTPException(
                    status_code=401,
                    detail="No HF token provided. Pass hf_token in the request or set HF_TOKEN env var.",
                )
            try:
                from huggingface_hub import InferenceClient

                model_used = f"{MODEL_ID} (API)"
                client = InferenceClient(token=hf_token, model=MODEL_ID)
                result = client.chat_completion(
                    messages,
                    max_tokens=request.max_tokens,
                    stream=False,
                    temperature=request.temperature,
                    top_p=request.top_p,
                )
                response_text = result.choices[0].message.content
            except HTTPException:
                raise
            except Exception as e:
                chat_errors_total.labels(error_type="hf_api_error").inc()
                chat_requests_total.labels(status="error", model_type=model_type).inc()
                raise HTTPException(status_code=500, detail=f"HF API error: {str(e)}")

        elapsed = time.time() - start_time
        chat_response_time_seconds.observe(elapsed)
        chat_requests_total.labels(status="success", model_type=model_type).inc()

        return ChatResponse(
            response=response_text,
            response_time=round(elapsed, 2),
            model_used=model_used,
        )
    finally:
        chat_active_requests.dec()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9008, reload=False)
