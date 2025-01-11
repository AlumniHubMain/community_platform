from conftest import authorized_client


def get_error_message(response, msg_prefix):
    error_msg_body = f"Error with status {response.status_code}. Details: {response.json()['detail']}"
    return msg_prefix + error_msg_body


def test_get_enums(authorized_client):

    response = authorized_client.get("/enums/EIntentType")
    assert response.status_code == 200, get_error_message(response, msg_prefix="Get enum info failed.")
    print(response.json())

