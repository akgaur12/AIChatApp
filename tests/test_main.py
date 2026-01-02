""" To run the tests, use the command: pytest -v """

def test_read_main(test_client):
    response = test_client.get("/docs")
    assert response.status_code == 200

def test_app_title(test_client):
    assert test_client.app.title == "AIChatApp"



