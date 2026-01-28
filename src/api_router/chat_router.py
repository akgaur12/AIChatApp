import logging, asyncio
from typing import List
from datetime import datetime, timezone

import json
from bson import ObjectId
from openai import OpenAI
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.utils import load_config
from src.deps import get_current_user
from src.pipelines.builder import pipeline
from src.clients.llm_client import llm_model
from src.llms.llm_parser import parse_response
from src.database import conversations_collection, messages_collection
from src.schemas import ConversationCreate, ConversationUpdate, Conversation, UserInput, UserQueryResponse, Message
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


logger = logging.getLogger(__name__)
cfg = load_config(filename="config.yml")

# Create API router
router = APIRouter(prefix="/chat", tags=["Chat"])


def get_current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()

def serialize_conversation(conversation, messages=None) -> Conversation:
    return Conversation(
        id=str(conversation["_id"]),
        user_id=conversation["user_id"],
        title=conversation.get("title"),
        messages=messages or [],
        message_count=conversation.get("message_count", 0),
        created_at=conversation.get("created_at"),
        updated_at=conversation.get("updated_at"),
    )

async def generate_title(user_query: str) -> str:
    try:        
        response = await llm_model.ainvoke([
                SystemMessage(content="You are a helpful assistant. Generate a short, 3-5 word title for a conversation that starts with the following user query. Do not use quotes."),
                HumanMessage(content=user_query)
            ]
        )
      
        # Remove quotes if present
        parsed = parse_response(response)
        title = parsed.content
        if title.startswith('"') and title.endswith('"'):
            title = title[1:-1]
        return title
    except Exception as e:
        logger.error(f"Error generating title: {e}", exc_info=True)
        return user_query[:50]


@router.post("/run_pipeline", response_model=UserQueryResponse, status_code=status.HTTP_201_CREATED)
async def execute_user_query(
    user_input: UserInput,
    current_user=Depends(get_current_user)
):
    user_prompt = user_input.user_query.strip()
    service_name = user_input.service_name.strip().lower()
    llm_messages = []
    
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
        
        # Load last 5 turns (10 messages) from DB history for context
        cursor = messages_collection.find({"chat_id": conversation_id}).sort("created_at", -1).limit(5)
        db_turns = []
        async for turn in cursor:
            db_turns.append(turn)
        
        db_turns.reverse() # Restore chronological order
        for turn in db_turns:
            llm_messages.append(HumanMessage(content=turn["user"]))
            llm_messages.append(AIMessage(content=turn["assistant"]))
    
    # Append current user message for LLM context
    llm_messages.append(HumanMessage(content=user_prompt))

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
    
    if not conversation_id:
        # Create new conversation
        title = await generate_title(user_prompt)
        new_conversation = {
            "user_id": user_id,
            "title": title,
            "message_count": 1, # First turn
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        result = await conversations_collection.insert_one(new_conversation)
        conversation_id = str(result.inserted_id)
        seq = 1
    else:
        # Atomic update of conversation metadata and sequence generation for existing chats
        updated_chat = await conversations_collection.find_one_and_update(
            {"_id": ObjectId(conversation_id)},
            {
                "$set": {"updated_at": timestamp},
                "$inc": {"message_count": 1}
            },
            return_document=True
        )
        if not updated_chat:
             raise HTTPException(status_code=404, detail="Conversation not found during update")
        seq = updated_chat.get("message_count", 0)

    # Insert turn document
    turn_doc = {
        "chat_id": conversation_id,
        "user": user_prompt,
        "assistant": assistant_content,
        "input_tokens": response.get("input_tokens", 0),
        "output_tokens": response.get("output_tokens", 0),
        "response_time": response.get("response_time", 0.0),
        "created_at": timestamp,
        "seq": seq
    }
    
    await messages_collection.insert_one(turn_doc)

    return {
        "conversation_id": conversation_id,
        "message": assistant_content
    }


@router.post("/run_pipeline/stream", status_code=status.HTTP_200_OK)
async def execute_user_query_streaming(
    user_input: UserInput,
    current_user=Depends(get_current_user)
):
    user_prompt = user_input.user_query.strip()
    service_name = user_input.service_name.strip().lower()
    llm_messages = []
    
    if service_name not in cfg["Services"]["SUPPORTED_SERVICES"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Service '{service_name}' not supported"
        )

    user_id = str(current_user["_id"])
    conversation_id = user_input.conversation_id
    
    # helper to validate and load history
    if conversation_id:
        if not ObjectId.is_valid(conversation_id):
             raise HTTPException(status_code=400, detail="Invalid conversation ID")
             
        existing_conversation = await conversations_collection.find_one({
            "_id": ObjectId(conversation_id),
            "user_id": user_id
        })
        
        if not existing_conversation:
             raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Load last 5 turns (10 messages) from DB history for context
        cursor = messages_collection.find({"chat_id": conversation_id}).sort("created_at", -1).limit(5)
        db_turns = []
        async for turn in cursor:
            db_turns.append(turn)
        
        db_turns.reverse() # Restore chronological order
        for turn in db_turns:
            llm_messages.append(HumanMessage(content=turn["user"]))
            llm_messages.append(AIMessage(content=turn["assistant"]))
    
    # Append current user message for LLM context
    llm_messages.append(HumanMessage(content=user_prompt))

    async def stream_generator():
        nonlocal conversation_id
        full_response = "" # The final total response (including links)
        streamed_response = "" # What we have streamed so far from LLM
        input_tokens = 0
        output_tokens = 0
        response_time = 0.0 # Placeholder, could measure start/end time
        
        start_time = datetime.now()

        try:
            async for event in pipeline.astream_events(
                {   
                    "service_name": service_name,
                    "user_input": user_prompt, 
                    "llm_messages": llm_messages
                },
                version="v2"
            ):
                kind = event["event"]

                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        streamed_response += content
                        yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                
                elif kind == "on_chat_model_end":
                    # Try to capture usage metadata if available
                    output = event["data"].get("output")
                    if output and hasattr(output, "usage_metadata"):
                        usage = output.usage_metadata
                        input_tokens = usage.get("input_tokens", 0) if hasattr(usage, "input_tokens") else None
                        output_tokens = usage.get("output_tokens", 0) if hasattr(usage, "output_tokens") else None

                elif kind == "on_chain_end":
                    # Capture the final state from the pipeline completion
                    # The event name for the main graph usually matches the graph name or is simply "LangGraph"
                    # We check if the output contains the keys we expect in our state
                    data = event["data"].get("output")
                    if data and isinstance(data, dict) and "llm_response" in data:
                        full_response = data["llm_response"]

        except Exception as e:
            logger.error(f"Error during streaming: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"
            return

        # If we didn't capture full_response from on_chain_end for some reason, fallback to streamed
        if not full_response:
            full_response = streamed_response
        
        # Check if there is extra content (e.g. links) that wasn't streamed
        if len(full_response) > len(streamed_response):
            diff = full_response[len(streamed_response):]
            if diff:
                yield f"data: {json.dumps({'type': 'content', 'content': diff})}\n\n"

        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        timestamp = get_current_timestamp()

        # DB persistence logic
        try:
            if not conversation_id:
                # Create new conversation
                title = await generate_title(user_prompt)
                new_conversation = {
                    "user_id": user_id,
                    "title": title,
                    "message_count": 1, 
                    "created_at": timestamp,
                    "updated_at": timestamp,
                }
                result = await conversations_collection.insert_one(new_conversation)
                conversation_id = str(result.inserted_id)
                seq = 1
            else:
                # Update existing conversation
                updated_chat = await conversations_collection.find_one_and_update(
                    {"_id": ObjectId(conversation_id)},
                    {
                        "$set": {"updated_at": timestamp},
                        "$inc": {"message_count": 1}
                    },
                    return_document=True
                )
                if updated_chat:
                    seq = updated_chat.get("message_count", 0)
                else:
                    # Fallback or error, though unlikely if checked before
                    seq = 1 

            # Insert turn document
            turn_doc = {
                "chat_id": conversation_id,
                "user": user_prompt,
                "assistant": full_response,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "response_time": response_time,
                "created_at": timestamp,
                "seq": seq
            }
            await messages_collection.insert_one(turn_doc)

            # Yield final metadata
            yield f"data: {json.dumps({'type': 'metadata', 'conversation_id': conversation_id})}\n\n"
            
        except Exception as e:
             logger.error(f"Error saving to DB: {e}", exc_info=True)
             yield f"data: {json.dumps({'type': 'error', 'detail': 'Error saving conversation'})}\n\n"

    return StreamingResponse(
        stream_generator(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # "X-Accel-Buffering": "no"     # Disable nginx buffering
        }
    )


@router.post("/conversations", response_model=Conversation, status_code=status.HTTP_201_CREATED)
async def create_new_conversation(
    conversation: ConversationCreate,
    current_user=Depends(get_current_user)
):
    new_conversation = {
        "user_id": str(current_user["_id"]),
        "title": conversation.title,
        "message_count": 0,
        "created_at": get_current_timestamp(),
        "updated_at": get_current_timestamp(),
    }
    result = await conversations_collection.insert_one(new_conversation)
    created_conversation = await conversations_collection.find_one({"_id": result.inserted_id})
    return serialize_conversation(created_conversation)


@router.get("/conversations", response_model=List[Conversation])
async def list_conversations(current_user=Depends(get_current_user)):
    user_id = str(current_user["_id"])
    conversations = []
    cursor = conversations_collection.find({"user_id": user_id}).sort("updated_at", -1)
    
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
    
    # Fetch turns
    messages = []
    cursor = messages_collection.find({"chat_id": conversation_id}).sort("created_at", 1)
    async for turn in cursor:
        messages.append(Message(
            id=str(turn["_id"]),
            chat_id=turn["chat_id"],
            user=turn["user"],
            assistant=turn["assistant"],
            input_tokens=turn.get("input_tokens", 0),
            output_tokens=turn.get("output_tokens", 0),
            response_time=turn.get("response_time", 0.0),
            created_at=turn["created_at"],
            seq=turn.get("seq")
        ))
        
    return serialize_conversation(conversation, messages=messages)


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

    # Delete conversation
    result = await conversations_collection.delete_one({
        "_id": ObjectId(conversation_id),
        "user_id": str(current_user["_id"])
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Delete associated messages
    await messages_collection.delete_many({"chat_id": conversation_id})

    return {"message": "Conversation and associated messages deleted successfully"}


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
