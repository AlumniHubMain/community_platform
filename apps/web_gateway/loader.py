from message_broker import BrokerFactory, BrokerType
# from config import settings
from web_gateway.settings import settings

# creating an instance of the broker (google_pubsub)
broker = BrokerFactory.create_broker(BrokerType.GOOGLE_PUBSUB,
                                     project_id=settings.google_cloud_project,
                                     credentials=settings.google_application_credentials)
