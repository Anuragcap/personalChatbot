from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import time
import os

app = FastAPI(
    title="Group 8 Personal Chatbot API",
    description="Backend API for the CS553 Personal Chatbot (Case Study 2)",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



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
    return HealthResponse(
        status="ok",
        backend_port=9008,
        timestamp=time.time()
    )

@app.get("/health", response_model=HealthResponse)
def health():
    """Health check for automated monitoring."""
    return HealthResponse(
        status="ok",
        backend_port=9008,
        timestamp=time.time()
    )

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    
    start_time = time.time()

    
    messages = [{"role": "system", "content": request.system_message}]
    for msg in request.history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": request.message})

    response_text = ""
    model_used = ""

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
            response_text = outputs[0]["generated_text"][len(prompt):].strip()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Local model error: {str(e)}")

    else:
        
        hf_token = request.hf_token or os.environ.get("HF_TOKEN")
        if not hf_token:
            raise HTTPException(
                status_code=401,
                detail="No HF token provided. Pass hf_token in the request or set HF_TOKEN env var."
            )
        try:
            from huggingface_hub import InferenceClient
            model_used = "meta-llama/Llama-3.2-3B-Instruct (API)"
            client = InferenceClient(token=hf_token, model="meta-llama/Llama-3.2-3B-Instruct")
            result = client.chat_completion(
                messages,
                max_tokens=request.max_tokens,
                stream=False,
                temperature=request.temperature,
                top_p=request.top_p,
            )
            response_text = result.choices[0].message.content
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"HF API error: {str(e)}")

    end_time = time.time()
    return ChatResponse(
        response=response_text,
        response_time=round(end_time - start_time, 2),
        model_used=model_used
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_backend:app", host="0.0.0.0", port=9008, reload=False)