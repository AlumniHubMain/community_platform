-- Enable UUID extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
        uid                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        name                VARCHAR(255) NOT NULL,
        surname             VARCHAR(255) NOT NULL,
        email               VARCHAR(255) UNIQUE NOT NULL,

        tg_id               INTEGER,
        tg_login            VARCHAR(255),
        linkedin_id         VARCHAR(255),
        bio                 TEXT,
        avatars             VARCHAR(255)[],

        created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        modified_at         TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        last_accessed_at    TIMESTAMP WITH TIME ZONE
);

-- Optional index for optimizing searches by email
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

------------

CREATE TABLE IF NOT EXISTS meetings (
    meeting_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title           VARCHAR(255) NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    scheduled_for   TIMESTAMP WITH TIME ZONE
);

------------

DO $$
BEGIN
   IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'meeting_role') THEN
      CREATE TYPE meeting_role AS ENUM ('mentor', 'mentee');
   END IF;
END $$;

CREATE TABLE IF NOT EXISTS user_meetings (
    user_id     UUID REFERENCES users(uid) ON DELETE CASCADE,
    meeting_id  UUID REFERENCES meetings(meeting_id) ON DELETE CASCADE,
    role        meeting_role,
    joined_at   TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id, meeting_id)
);

-- Optional index on the join table for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_meetings_user ON user_meetings (user_id);
CREATE INDEX IF NOT EXISTS idx_user_meetings_meeting ON user_meetings (meeting_id);
