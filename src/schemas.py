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


class Message(BaseModel):
    user: str
    assistant: str
    input_tokens: int
    output_tokens: int
    response_time: float

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
    created_at: str
    updated_at: str


class UserInput(BaseModel):
    service_name: str
    user_query: str
    conversation_id: str | None = None

class UserQueryResponse(BaseModel):
    conversation_id: str
    message: str
