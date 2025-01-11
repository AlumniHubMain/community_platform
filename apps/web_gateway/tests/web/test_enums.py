from conftest import authorized_client
from utils import assert_response_status


def test_get_enums(authorized_client):

    response = authorized_client.get("/enums/EIntentType")
    assert_response_status(response, expected_status_code=200, msg_prefix="Get enum info failed.")

