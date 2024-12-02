CREATE TYPE E_INTENT_TYPE AS ENUM ('connect', 'mentoring', 'mock_interview', 'help_request', 'referal');
CREATE TYPE E_MEETING_FORMAT AS ENUM ('offline', 'online', 'any');

CREATE TABLE IF NOT EXISTS forms (
    created_at                              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at                              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id                                      BIGSERIAL PRIMARY KEY,
    user_id                                 BIGSERIAL REFERENCES users (id),
    form                                    TEXT,
    description                             VARCHAR(1000),
    intent_type                             E_INTENT_TYPE,
    meeting_format                          E_MEETING_FORMAT,
    calendar                                VARCHAR(200),
    available_meetings_count                INT8
);