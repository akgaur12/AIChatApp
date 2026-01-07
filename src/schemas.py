"""
This file contains all the Pydantic models used in the application.
BaseModel: A strict gatekeeper at the API door. BaseModel ensures your app only works with valid, typed, trusted data.
"""

from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ResetPasswordRequest(BaseModel):
    old_password: str = Field(min_length=6)
    new_password: str = Field(min_length=6)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordWithOTP(BaseModel):
    email: EmailStr
    otp: str
    new_password: str = Field(min_length=6)


class Message(BaseModel):
    id: str | None = None
    chat_id: str
    user: str
    assistant: str
    created_at: str
    seq: int | None = None

class ConversationBase(BaseModel):
    title: str = Field(
        default="New Chat",
        min_length=1,
        max_length=60,
        description="New conversation title (1-60 characters)"
    )

class ConversationCreate(ConversationBase):
    pass

class ConversationUpdate(ConversationBase):
    pass

class Conversation(ConversationBase):
    id: str
    user_id: str
    messages: list[Message] = []
    message_count: int = 0
    created_at: str
    updated_at: str


class UserInput(BaseModel):
    service_name: str = "chat"
    user_query: str
    conversation_id: str | None = None

class UserQueryResponse(BaseModel):
    conversation_id: str
    message: str
