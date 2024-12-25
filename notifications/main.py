import asyncio

from config import settings
from loader import broker
from src.logic.incoming_message import message_handler


async def main():
    # subscribing to the notification topic
    await broker.subscribe(settings.ps_notification_sub_name, message_handler)


if __name__ == "__main__":
    asyncio.run(main())
