import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from datetime import datetime

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
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })
        
        response = test_client.post("/chat/conversations", json={"title": "New Chat"})
        
        assert response.status_code == 201
        assert response.json()["title"] == "New Chat"
    
    app.dependency_overrides = {}

def test_list_conversations(test_client, mock_user_id):
    from src.api_router.chat_router import get_current_user
    from main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user

    with patch("src.api_router.chat_router.conversations_collection") as mock_collection:
        # Mock cursor for find
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__.return_value = [
            {
                "_id": ObjectId(),
                "user_id": mock_user_id,
                "title": "Chat 1",
                "messages": [],
                "created_at": "2023-01-01",
                "updated_at": "2023-01-01"
            },
            {
                "_id": ObjectId(),
                "user_id": mock_user_id,
                "title": "Chat 2",
                "messages": [],
                "created_at": "2023-01-02",
                "updated_at": "2023-01-02"
            }
        ]
        mock_collection.find.return_value = mock_cursor
        
        response = test_client.get("/chat/conversations")
        
        assert response.status_code == 200
        assert len(response.json()) == 2
        
    app.dependency_overrides = {}

def test_execute_user_query_new_conversation(test_client, mock_user_id):
    from src.api_router.chat_router import get_current_user
    from main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    # Mock LLM and Database
    with patch("src.api_router.chat_router.conversations_collection") as mock_collection, \
         patch("src.api_router.chat_router.pipeline") as mock_pipeline, \
         patch("src.api_router.chat_router.llm_model") as mock_llm_model, \
         patch("src.api_router.chat_router.cfg", {"Services": {"SUPPORTED_SERVICES": ["chatgpt"]}}): # Mock config
        
        # Mock Title Generation
        mock_llm_model.ainvoke = AsyncMock(return_value=MagicMock(content="Generated Title"))
        
        # Mock Pipeline Response
        mock_pipeline.ainvoke = AsyncMock(return_value={"llm_response": "Hello User"})
        
        # Mock DB Insert
        mock_inserted = MagicMock()
        mock_inserted.inserted_id = ObjectId()
        mock_collection.insert_one = AsyncMock(return_value=mock_inserted)
        
        response = test_client.post("/chat/execute_user_query", json={
            "user_query": "Hello",
            "service_name": "ChatGPT"
        })
        
        if response.status_code != 201:
             print(response.json())

        assert response.status_code == 201
        json_resp = response.json()
        assert json_resp["message"] == "Hello User"
        assert "conversation_id" in json_resp
        
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
            {"_id": chat_id, "user_id": mock_user_id, "title": "Renamed Title", "messages": [], "created_at": "", "updated_at": ""} # Second call for returning updated
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

    with patch("src.api_router.chat_router.conversations_collection") as mock_collection:
        mock_result = MagicMock()
        mock_result.deleted_count = 1
        mock_collection.delete_one = AsyncMock(return_value=mock_result)

        response = test_client.delete(f"/chat/conversations/{str_chat_id}")
        
        assert response.status_code == 200
        assert response.json() == {"message": "Conversation deleted successfully"}

    app.dependency_overrides = {}
