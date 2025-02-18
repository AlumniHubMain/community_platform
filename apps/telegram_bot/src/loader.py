from aiogram import Bot, Dispatcher

from message_broker import BrokerFactory, BrokerType
from .config import settings


bot = Bot(token=settings.bot_token.get_secret_value())
dp: Dispatcher = Dispatcher()

# creating an instance of the broker (google_pubsub)
broker = BrokerFactory.create_broker(BrokerType.GOOGLE_PUBSUB,
                                     project_id=settings.ps_project_id,
                                     credentials=settings.ps_credentials)
