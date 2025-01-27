from loguru import logger
import asyncio

from config import settings
from src.pubsub.handlers import handle_profile_task
from loader import broker


async def main():
    try:
        logger.info("Starting LinkedIn profile validator...")
        
        # Создаем задачу для подписки на PubSub
        subscription_task = asyncio.create_task(
            broker.subscribe(
                settings.pubsub_linkedin_tasks_sub,
                handle_profile_task
            )
        )
        
        logger.info("Started listening for LinkedIn profile tasks")
        
        # Держим приложение активным
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        raise
    finally:
        logger.info("Shutting down...")


if __name__ == "__main__":
    asyncio.run(main())


    # Example:
    # broker = BrokerFactory.create_broker(BrokerType.GOOGLE_PUBSUB,
    #                                      project_id="my-project",
    #                                      credentials=settings.ps_credentials)
    # await broker.subscribe("my-topic-sub", message_handler)
    # await broker.publish("my-topic", message)

    # asyncio.create_task(broker.subscribe(settings.ps_notification_tg_sub_name, message_handler))
