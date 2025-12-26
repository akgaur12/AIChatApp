from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ResetPasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6)


class Message(BaseModel):
    user: str
    assistant: str

class ConversationBase(BaseModel):
    title: str = "New Chat"

class ConversationCreate(ConversationBase):
    pass

class ConversationUpdate(ConversationBase):
    pass

class Conversation(ConversationBase):
    id: str
    user_id: str
    messages: list[Message] = []
    created_at: str
    updated_at: str


class UserInput(BaseModel):
    service_name: str
    user_query: str
    conversation_id: str | None = None

class UserQueryResponse(BaseModel):
    conversation_id: str
    message: str
