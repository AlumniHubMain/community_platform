
def get_error_message(response, expected_status_code, msg_prefix=None):
    error_msg_body = f"Error. Recieved status code {response.status_code}, but expected {expected_status_code}."
    json_response = response.json()
    if 'detail' in json_response:
        error_msg_body += f" Details: {json_response['detail']}"

    if msg_prefix is None:
        return error_msg_body
    return msg_prefix + error_msg_body


def assert_response_status(response, expected_status_code=200, msg_prefix=None):
    assert response.status_code == expected_status_code, get_error_message(response, expected_status_code=200, msg_prefix=msg_prefix)
