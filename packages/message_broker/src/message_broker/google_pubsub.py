import asyncio

from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.subscriber.message import Message

from typing import Union, Callable, Awaitable

from .broker import MessageBroker, SchemaType


class GooglePubSubBroker(MessageBroker[Message]):
    """Implements message broker interface using Google Cloud Pub/Sub"""

    def __init__(self, project_id: str, credentials: any):
        """Initialize Pub/Sub client with project ID and credentials
        Args:
            project_id: Google Cloud project ID
            credentials: Google Cloud credentials
        """
        self.project_id = project_id
        self.publisher = pubsub_v1.PublisherClient(credentials=credentials)
        self.subscriber = pubsub_v1.SubscriberClient(credentials=credentials)

    async def publish(self, topic: str, message: SchemaType) -> str:
        """Publish message to specified topic
        Args:
            topic: name of the message_broker topic to publish
            message: pydantic model message to publish (based on BaseModel)
        Returns:
            Pub/Sub message ID, type str
        """
        topic_path = self.publisher.topic_path(self.project_id, topic)
        message_data = message.model_dump_json().encode('utf-8')

        try:
            future = self.publisher.publish(topic_path, message_data)
            return future.result()
        except Exception as e:
            raise Exception(f"Publish error: {str(e)}")

    async def subscribe(
            self,
            sub_topic: str,
            callback: Union[Callable[[Message], None], Callable[[Message], Awaitable[None]]]
    ) -> None:
        """Subscribe to messages from specified subscription.

                Args:
                    sub_topic: Name of the subscription to listen to
                    callback: Function to process received messages. Can be either synchronous or asynchronous.
                             For synchronous: Callable[[Message], None]
                             For asynchronous: Callable[[Message], Awaitable[None]]
                """
        subscription_path = self.subscriber.subscription_path(
            self.project_id, sub_topic
        )

        # Saving the main loop
        main_loop = asyncio.get_running_loop()

        def sync_wrapper(message: Message) -> None:
            """Synchronous message processing wrapper"""
            try:
                if asyncio.iscoroutinefunction(callback):
                    # We run the coroutine in the main loop
                    future = asyncio.run_coroutine_threadsafe(
                        callback(message),
                        main_loop
                    )
                    # Waiting for the result
                    future.result(timeout=30)
                else:
                    callback(message)
            except Exception as e:
                print(f"Error in the message handler: {str(e)}")
                message.nack()

        # Launching a subscription without blocking
        streaming_pull_future = self.subscriber.subscribe(subscription_path, callback=sync_wrapper)

        def on_error(future):
            try:
                future.result()
            except Exception as e:
                print(f"Subscription error: {str(e)}")

        streaming_pull_future.add_done_callback(on_error)
