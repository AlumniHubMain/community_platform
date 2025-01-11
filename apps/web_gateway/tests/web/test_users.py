from conftest import authorized_client
from utils import assert_response_status


def test_create_user(authorized_client):
    # TODO: @ilyabiro - Refactor it and check response output. Temporal solution for gateway tests healthcheck
    user_minimal_data = """{
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "ivanovi@mail.ru",
        "requests_to_community": ["friendship"],
        "avatars": [],
        "about": "",
        "interests": [],
        "linkedin_link": "",
        "telegram_name": "da",
        "telegram_id": 1,
        "expertise_area": null,
        "specialisation": null,
        "grade": null,
        "industry": null,
        "skills": null,
        "current_company": null,
        "company_services": null,
        "location": null,
        "referral": null,
        "available_meetings_pendings_count": 0,
        "available_meetings_confirmations_count": 0,
        "who_to_date_with": "anyone",
        "who_sees_profile": "anyone",
        "who_sees_current_job": "anyone",
        "who_sees_contacts": "anyone",
        "who_sees_calendar": "anyone"
    }"""
    response = authorized_client.post("/user", content=user_minimal_data)
    assert_response_status(response, expected_status_code=200, msg_prefix="Create user failed.")
