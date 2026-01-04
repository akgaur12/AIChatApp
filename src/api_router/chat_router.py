import logging, asyncio
from typing import List
from datetime import datetime, timezone

from bson import ObjectId
from openai import OpenAI
from fastapi import APIRouter, Depends, HTTPException, status

from src.utils import load_config
from src.deps import get_current_user
from src.pipelines.builder import pipeline
from src.services.models import llm_model
from src.database import conversations_collection
from src.schemas import ConversationCreate, ConversationUpdate, Conversation, UserInput, UserQueryResponse


logger = logging.getLogger(__name__)
cfg = load_config(filename="config.yml")

# Create API router
router = APIRouter(prefix="/chat", tags=["Chat"])


def get_current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()

def serialize_conversation(conversation) -> Conversation:
    return Conversation(
        id=str(conversation["_id"]),
        user_id=conversation["user_id"],
        title=conversation.get("title"),
        messages=conversation.get("messages", []),
        created_at=conversation.get("created_at"),
        updated_at=conversation.get("updated_at"),
    )

async def generate_title(user_query: str) -> str:
    try:        
        response = await llm_model.ainvoke([
                {
                    "role": "system", 
                    "content": "You are a helpful assistant. Generate a short, 3-5 word title for a conversation that starts with the following user query. Do not use quotes."
                },
                {"role": "user", "content": user_query}
            ],  
            max_tokens=100, 
            temperature=0.7 
        )
      
        # Remove quotes if present
        title = response.content
        if title.startswith('"') and title.endswith('"'):
            title = title[1:-1]
        return title
    except Exception as e:
        logger.error(f"Error generating title: {e}", exc_info=True)
        return user_query[:50]


@router.post("/execute_user_query", response_model=UserQueryResponse, status_code=status.HTTP_201_CREATED)
async def execute_user_query(
    user_input: UserInput,
    current_user=Depends(get_current_user)
):
    user_prompt = user_input.user_query.strip()
    service_name = user_input.service_name.strip().lower()
    messages = []
    
    if service_name not in cfg["Services"]["SUPPORTED_SERVICES"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Service '{service_name}' not supported"
        )

    user_id = str(current_user["_id"])
    conversation_id = user_input.conversation_id
    
    if conversation_id:
        if not ObjectId.is_valid(conversation_id):
             raise HTTPException(status_code=400, detail="Invalid conversation ID")
             
        existing_conversation = await conversations_collection.find_one({
            "_id": ObjectId(conversation_id),
            "user_id": user_id
        })
        
        if not existing_conversation:
             raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Load existing messages from DB history
        # Transform to OpenAI format for context
        db_messages = existing_conversation.get("messages", [])
        for msg in db_messages:
            messages.append({"role": "user", "content": msg.get("user")})
            messages.append({"role": "assistant", "content": msg.get("assistant")})
    
    # Append current user message for LLM context
    messages.append({"role": "user", "content": user_prompt})

    # taking last 10 messages (5 turns) for context
    llm_messages = messages[-10:] if len(messages) > 10 else messages
    
    # Call pipeline
    response = await pipeline.ainvoke(
        {   
            "service_name": service_name,
            "user_input": user_prompt, 
            "llm_messages": llm_messages
        }
    )
    
    assistant_content = response["llm_response"]
    timestamp = get_current_timestamp()
    
    # New message entry to save
    new_message_entry = {
        "user": user_prompt,
        "assistant": assistant_content
    }
    
    if conversation_id:
        # Update existing conversation
        await conversations_collection.update_one(
            {"_id": ObjectId(conversation_id)},
            {
                "$push": {"messages": new_message_entry},
                "$set": {"updated_at": timestamp}
            }
        )
    else:
        # Create new conversation
        # Generate title using LLM
        title = await generate_title(user_prompt)
        
        new_conversation = {
            "user_id": user_id,
            "title": title,
            "messages": [new_message_entry],
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        result = await conversations_collection.insert_one(new_conversation)
        conversation_id = str(result.inserted_id)

    # Return JSON with id and message
    # Note: We need to change response_model to dict or specific schema to support this return type correctly
    # But for now user asked to return just content in previous turn, 
    # but now in plan we agreed to return object.
    # The function signature still has `response_model=str` in the replacement content above?
    # Wait, I need to update response_model too.
    
    return {
        "conversation_id": conversation_id,
        "message": assistant_content
    }


@router.post("/conversations", response_model=Conversation, status_code=status.HTTP_201_CREATED)
async def create_new_conversation(
    conversation: ConversationCreate,
    current_user=Depends(get_current_user)
):
    new_conversation = {
        "user_id": str(current_user["_id"]),
        "title": conversation.title,
        "messages": [],
        "created_at": get_current_timestamp(),
        "updated_at": get_current_timestamp(),
    }
    result = await conversations_collection.insert_one(new_conversation)
    created_conversation = await conversations_collection.find_one({"_id": result.inserted_id})
    return serialize_conversation(created_conversation)


@router.get("/conversations", response_model=List[Conversation])
async def list_conversations(current_user=Depends(get_current_user)):
    conversations = []
    cursor = conversations_collection.find({"user_id": str(current_user["_id"])})
    async for conversation in cursor:
        conversations.append(serialize_conversation(conversation))
    return conversations


@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversion_by_id(
    conversation_id: str,
    current_user=Depends(get_current_user)
):
    if not ObjectId.is_valid(conversation_id):
        raise HTTPException(status_code=400, detail="Invalid conversation ID")
        
    conversation = await conversations_collection.find_one({
        "_id": ObjectId(conversation_id),
        "user_id": str(current_user["_id"])
    })
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    return serialize_conversation(conversation)


@router.put("/conversations/{conversation_id}", response_model=Conversation)
async def update_exiting_conversion(
    conversation_id: str,
    conversation_update: ConversationUpdate,
    current_user=Depends(get_current_user)
):
    if not ObjectId.is_valid(conversation_id):
        raise HTTPException(status_code=400, detail="Invalid conversation ID")

    # Check if conversation exists and belongs to user
    existing_conversation = await conversations_collection.find_one({
        "_id": ObjectId(conversation_id),
        "user_id": str(current_user["_id"])
    })
    if not existing_conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    update_data = {k: v for k, v in conversation_update.dict(exclude_unset=True).items()}
    update_data["updated_at"] = get_current_timestamp()

    await conversations_collection.update_one(
        {"_id": ObjectId(conversation_id)},
        {"$set": update_data}
    )

    updated_conversation = await conversations_collection.find_one({"_id": ObjectId(conversation_id)})
    return serialize_conversation(updated_conversation)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_200_OK)
async def delete_conversion_by_id(
    conversation_id: str,
    current_user=Depends(get_current_user)
):
    if not ObjectId.is_valid(conversation_id):
        raise HTTPException(status_code=400, detail="Invalid conversation ID")

    result = await conversations_collection.delete_one({
        "_id": ObjectId(conversation_id),
        "user_id": str(current_user["_id"])
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"message": "Conversation deleted successfully"}


@router.put("/conversations/{conversation_id}/rename", response_model=Conversation, status_code=status.HTTP_200_OK)
async def rename_conversation_title(
    conversation_id: str,
    payload: ConversationCreate,
    current_user=Depends(get_current_user)
):
    new_title = payload.title.strip()

    if not ObjectId.is_valid(conversation_id):
        raise HTTPException(status_code=400, detail="Invalid conversation ID")

    if not new_title or not new_title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    # Ensure conversation belongs to the user
    conversation = await conversations_collection.find_one({
        "_id": ObjectId(conversation_id),
        "user_id": str(current_user["_id"])
    })

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await conversations_collection.update_one(
        {"_id": ObjectId(conversation_id)},
        {
            "$set": {
                "title": new_title.strip(),
                "updated_at": get_current_timestamp()
            }
        }
    )

    updated_conversation = await conversations_collection.find_one(
        {"_id": ObjectId(conversation_id)}
    )

    return serialize_conversation(updated_conversation)
