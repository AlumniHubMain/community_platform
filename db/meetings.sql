CREATE TYPE USER_ROLE AS ENUM ('organizer', 'attendee');
CREATE TYPE AGREEMENT AS ENUM ('confirmed', 'tentative', 'declined');
CREATE TYPE MEETING_STATUS AS ENUM ('new', 'confirmed', 'archived');

CREATE TABLE IF NOT EXISTS meetings (
    id                      BIGSERIAL PRIMARY KEY,

    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    description             TEXT,
    location                VARCHAR(200),
    scheduled_time          TIMESTAMP WITH TIME ZONE,
    status                  MEETING_STATUS
);

CREATE TABLE IF NOT EXISTS user_meetings
(
    uid             BIGSERIAL REFERENCES users(id) ON DELETE CASCADE,
    meeting_id      BIGSERIAL REFERENCES meetings(id) ON DELETE CASCADE,

    role            USER_ROLE NOT NULL,
    agreement       AGREEMENT,

    PRIMARY KEY (uid, meeting_id)
);
