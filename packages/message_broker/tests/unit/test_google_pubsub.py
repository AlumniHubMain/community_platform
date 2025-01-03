from pydantic import BaseModel

from message_broker.google_pubsub import GooglePubSubBroker


class Message(BaseModel):
    data: str


async def test_google_pubsub(google_pubsub_config, google_pubsub_emulator):
    broker = GooglePubSubBroker(
        project_id=google_pubsub_config.project,
        credentials=None,
    )
    await broker.publish("test-topic", Message(data="test-data"))
