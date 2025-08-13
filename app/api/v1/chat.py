from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models.chat_with_ai import ChatWithAI, ChatRoleEnum
from app.models.scan import Scan
from app.schemas.chat_with_ai import (
    ChatRequest,
    ChatWithAIRead,
    ChatPostResponse,
)
from app.services.health_profile import health_profile as hp_service
from app.services.chat import chat as chat_service


router = APIRouter()


@router.get("/{scan_id}", response_model=List[ChatWithAIRead])
def get_chat_history(scan_id: UUID, db: Session = Depends(get_db)):
    """Return all chat messages for a scan, ordered by timestamp."""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    messages = (
        db.query(ChatWithAI)
        .filter(ChatWithAI.scan_id == scan_id)
        .order_by(ChatWithAI.timestamp.asc())
        .all()
    )
    return [ChatWithAIRead.model_validate(m) for m in messages]


@router.post(
    "/{scan_id}", response_model=ChatPostResponse, status_code=status.HTTP_201_CREATED
)
def post_chat_message(
    scan_id: UUID,
    body: Optional[ChatRequest] = None,
    message: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Save user message, generate concise assistant reply with GPT-4o-mini, persist both, and return them.

    Note: No current_user validation for this specific feature as requested.
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    resolved_message = (
        (body.message if body and body.message is not None else message) or ""
    ).strip()
    if not resolved_message:
        raise HTTPException(
            status_code=422, detail="'message' is required in body or query"
        )

    user_message = ChatWithAI(
        user_id=scan.user_id,
        scan_id=scan_id,
        role=ChatRoleEnum.user,
        message=resolved_message,
    )
    db.add(user_message)
    db.flush()

    profile = hp_service.get_health_profile_by_user(db, scan.user_id)
    profile_dict = None
    if profile:
        profile_dict = {
            "allergies": profile.allergies or [],
            "chronic_conditions": profile.chronic_conditions or [],
            "dietary_preferences": profile.dietary_preferences or [],
        }

    system_prompt = chat_service.build_chat_system_prompt(
        product_name=scan.product_name,
        ingredients=scan.parsed_ingredients or [],
        summary_explanation=scan.summary_explanation,
        profile_dict=profile_dict,
    )

    history: List[ChatWithAI] = (
        db.query(ChatWithAI)
        .filter(ChatWithAI.scan_id == scan_id)
        .order_by(ChatWithAI.timestamp.asc())
        .all()
    )

    oa_messages = [{"role": "system", "content": system_prompt}]
    for m in history:
        oa_messages.append({"role": m.role.value, "content": m.message})

    ai_content = chat_service.generate_assistant_reply(oa_messages)

    assistant_message = ChatWithAI(
        user_id=scan.user_id,
        scan_id=scan_id,
        role=ChatRoleEnum.assistant,
        message=ai_content,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)

    return ChatPostResponse(
        messages=[
            ChatWithAIRead.model_validate(user_message),
            ChatWithAIRead.model_validate(assistant_message),
        ]
    )
