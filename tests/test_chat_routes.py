import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from datetime import datetime, timezone
from src.schemas import Message

# Mock Auth Dependency
async def mock_get_current_user():
    return {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "email": "test@example.com"
    }
    
@pytest.fixture
def mock_user_id():
    return "507f1f77bcf86cd799439011"

def test_create_conversation(test_client, mock_user_id):
    from src.api_router.chat_router import get_current_user
    from main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    with patch("src.api_router.chat_router.conversations_collection") as mock_collection:
        mock_inserted = MagicMock()
        mock_inserted.inserted_id = ObjectId()
        mock_collection.insert_one = AsyncMock(return_value=mock_inserted)
        
        # Mock find_one to return the created conversation
        mock_collection.find_one = AsyncMock(return_value={
            "_id": mock_inserted.inserted_id,
            "user_id": mock_user_id,
            "title": "New Chat",
            "message_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        
        response = test_client.post("/chat/conversations", json={"title": "New Chat"})
        
        assert response.status_code == 201
        assert response.json()["title"] == "New Chat"
        assert response.json()["message_count"] == 0
    
    app.dependency_overrides = {}

def test_list_conversations(test_client, mock_user_id):
    from src.api_router.chat_router import get_current_user
    from main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user

    with patch("src.api_router.chat_router.conversations_collection") as mock_collection:
        # Mock cursor for find
        mock_cursor = MagicMock()
        mock_cursor.__aiter__.return_value = [
            {
                "_id": ObjectId(),
                "user_id": mock_user_id,
                "title": "Chat 1",
                "message_count": 2,
                "created_at": "2023-01-01",
                "updated_at": "2023-01-01"
            },
            {
                "_id": ObjectId(),
                "user_id": mock_user_id,
                "title": "Chat 2",
                "message_count": 5,
                "created_at": "2023-01-02",
                "updated_at": "2023-01-02"
            }
        ]
        # Chaining find().sort() should return the mock_cursor
        mock_collection.find.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        
        response = test_client.get("/chat/conversations")
        
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["message_count"] == 2
        
    app.dependency_overrides = {}

def test_execute_user_query_new_conversation(test_client, mock_user_id):
    from src.api_router.chat_router import get_current_user
    from main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    # Mock LLM and Database
    with patch("src.api_router.chat_router.conversations_collection") as mock_conv_collection, \
         patch("src.api_router.chat_router.messages_collection") as mock_msg_collection, \
         patch("src.api_router.chat_router.pipeline") as mock_pipeline, \
         patch("src.api_router.chat_router.llm_model") as mock_llm_model, \
         patch("src.api_router.chat_router.cfg", {"Services": {"SUPPORTED_SERVICES": ["chat"]}}): # Mock config
        
        # Mock Title Generation
        mock_llm_model.ainvoke = AsyncMock(return_value=MagicMock(content="Generated Title"))
        
        # Mock Pipeline Response
        mock_pipeline.ainvoke = AsyncMock(return_value={"llm_response": "Hello User"})
        
        # Mock DB Inserts
        mock_inserted = MagicMock()
        mock_inserted.inserted_id = ObjectId()
        mock_conv_collection.insert_one = AsyncMock(return_value=mock_inserted)
        mock_msg_collection.insert_one = AsyncMock()
        
        response = test_client.post("/chat/execute_user_query", json={
            "user_query": "Hello",
            "service_name": "chat"
        })
        
        assert response.status_code == 201
        json_resp = response.json()
        assert json_resp["message"] == "Hello User"
        assert "conversation_id" in json_resp
        
        mock_conv_collection.insert_one.assert_called_once()
        mock_msg_collection.insert_one.assert_called_once()
        
    app.dependency_overrides = {}

def test_get_conversation_by_id(test_client, mock_user_id):
    from src.api_router.chat_router import get_current_user
    from main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    chat_id = ObjectId()
    str_chat_id = str(chat_id)
    
    with patch("src.api_router.chat_router.conversations_collection") as mock_conv_collection, \
         patch("src.api_router.chat_router.messages_collection") as mock_msg_collection:
        
        mock_conv_collection.find_one = AsyncMock(return_value={
            "_id": chat_id,
            "user_id": mock_user_id,
            "title": "Test Chat",
            "message_count": 1,
            "created_at": "2023-01-01",
            "updated_at": "2023-01-01"
        })
        
        mock_cursor = MagicMock()
        mock_cursor.__aiter__.return_value = [
            {
                "_id": ObjectId(),
                "chat_id": str_chat_id,
                "user": "Hello",
                "assistant": "Hi there",
                "created_at": "2023-01-01",
                "seq": 1
            }
        ]
        # Chaining find().sort()
        mock_msg_collection.find.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        
        response = test_client.get(f"/chat/conversations/{str_chat_id}")
        
        assert response.status_code == 200
        json_resp = response.json()
        assert json_resp["id"] == str_chat_id
        assert len(json_resp["messages"]) == 1
        assert json_resp["messages"][0]["user"] == "Hello"

    app.dependency_overrides = {}

def test_rename_conversation(test_client, mock_user_id):
    from src.api_router.chat_router import get_current_user
    from main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user

    chat_id = ObjectId()
    str_chat_id = str(chat_id)

    with patch("src.api_router.chat_router.conversations_collection") as mock_collection:
        # User owns conversation
        mock_collection.find_one = AsyncMock(side_effect=[
            {"_id": chat_id, "user_id": mock_user_id}, # First call for checking ownership
            {"_id": chat_id, "user_id": mock_user_id, "title": "Renamed Title", "message_count": 0, "created_at": "", "updated_at": ""} # Second call for returning updated
        ])
        mock_collection.update_one = AsyncMock()

        response = test_client.put(f"/chat/conversations/{str_chat_id}/rename", json={"title": "Renamed Title"})
        
        assert response.status_code == 200
        assert response.json()["title"] == "Renamed Title"

    app.dependency_overrides = {}

def test_delete_conversation(test_client, mock_user_id):
    from src.api_router.chat_router import get_current_user
    from main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user

    chat_id = ObjectId()
    str_chat_id = str(chat_id)

    with patch("src.api_router.chat_router.conversations_collection") as mock_conv_collection, \
         patch("src.api_router.chat_router.messages_collection") as mock_msg_collection:
        
        mock_result = MagicMock()
        mock_result.deleted_count = 1
        mock_conv_collection.delete_one = AsyncMock(return_value=mock_result)
        mock_msg_collection.delete_many = AsyncMock()

        response = test_client.delete(f"/chat/conversations/{str_chat_id}")
        
        assert response.status_code == 200
        assert response.json() == {"message": "Conversation and associated messages deleted successfully"}
        
        mock_msg_collection.delete_many.assert_called_once_with({"chat_id": str_chat_id})

    app.dependency_overrides = {}
