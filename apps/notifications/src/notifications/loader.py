from message_broker import BrokerFactory, BrokerType
from notifications.config import settings

# creating an instance of the broker (google_pubsub)
broker = BrokerFactory.create_broker(BrokerType.GOOGLE_PUBSUB,
                                     project_id=settings.ps_project_id,
                                     credentials=settings.ps_credentials)
