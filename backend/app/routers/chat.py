from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_chat_service import answer_question

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=422, detail="Question cannot be empty.")

    result = answer_question(
        question=request.question,
        company=request.company,
        fiscal_year=request.fiscal_year,
    )
    return ChatResponse(**result)