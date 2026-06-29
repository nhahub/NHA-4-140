from pydantic import BaseModel


class ChatSessionRequest(BaseModel):
    context_ad_id: str | None = None
