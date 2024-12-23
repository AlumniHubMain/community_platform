
def test_health(telegram_bot_client):
    response = telegram_bot_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}



def test_web(telegram_bot_client):
    response = telegram_bot_client.post("/webhook", json={
        "update_id": 42,
        "message": {
            "message_id": 42,
            "date": 1582324717,
            "text": "test",
            "chat": {"id": 42, "type": "private"},
            "from": {"id": 42, "is_bot": False, "first_name": "Test"},
        },
    })

    assert response.status_code == 200