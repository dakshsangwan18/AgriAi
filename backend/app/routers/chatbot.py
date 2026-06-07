from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.services.chatbot_service import get_chatbot_service
from typing import List, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.logging_config import logger
import asyncio

router = APIRouter()
chatbot_service = get_chatbot_service()
limiter = Limiter(key_func=get_remote_address)

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str
    timestamp: str

@router.post("/ask", response_model=ChatResponse)
@limiter.limit("10/minute")  # Reduced to stay under Groq free tier limit
async def ask_question(request: Request, chat_request: ChatRequest):

    from datetime import datetime

    if not chat_request.message or chat_request.message.strip() == "":
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        if chat_request.history and len(chat_request.history) > 0:
            history_list = [{"role": msg.role, "content": msg.content} for msg in chat_request.history]
            response = await asyncio.to_thread(
                chatbot_service.get_response_with_history, chat_request.message, history_list
            )
        else:
            response = await asyncio.to_thread(
                chatbot_service.get_response, chat_request.message
            )

        return {
            "response": response,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chatbot /ask failed: {e}")
        raise HTTPException(status_code=500, detail="Chatbot request failed")

@router.get("/suggestions")
@limiter.limit("100/hour")
async def get_suggestions(request: Request):
    
    return {
        "suggestions": [
            "When is the best time to plant wheat?",
            "How do I treat tomato leaf blight?",
            "What fertilizer is best for rice?",
            "How often should I irrigate my crops?",
            "How to control aphids organically?",
            "What are the symptoms of nitrogen deficiency?",
            "Best crops for monsoon season?",
            "How to improve soil fertility naturally?"
        ]
    }
