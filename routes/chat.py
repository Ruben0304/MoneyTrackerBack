from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

from external_services import conversar

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = "gemini-2.5-flash"  # Default model
    system_prompt: Optional[str] = None
    streaming: Optional[bool] = False

class ChatResponse(BaseModel):
    response: str
    model: str

@router.post("/chat", response_model=ChatResponse)
async def chat_with_gemini(request: ChatRequest):
    """
    Chat with Google's Gemini AI model
    """
    try:
        response = await conversar(
            modelo=request.model,
            pregunta=request.message,
            system_prompt=request.system_prompt,
            streaming=request.streaming
        )
        
        return ChatResponse(
            response=response,
            model=request.model
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error communicating with Gemini: {str(e)}"
        )