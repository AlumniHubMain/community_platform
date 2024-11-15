"""Pub/Sub maybe need an adapter"""

import asyncio
import json

from google.cloud import pubsub_v1


class GoogleQueueManager:
    """GoogleQueueManager"""

    def __init__(self):
        self.config = None
        self.publisher = None

    async def put_to_queue(self, topic_path, data):
        """Puts to google queue"""
        message_json = json.dumps(data)
        message_bytes = message_json.encode("utf-8")
        topic_path = self.publisher.topic_path(self.config.active_config.project_id, topic_path)
        future = self.publisher.publish(topic_path, data=message_bytes)
        message_id = await asyncio.wrap_future(future)
        return message_id

    async def initialize(self, config):
        """Async init"""
        self.config = config
        self.publisher = pubsub_v1.PublisherClient()
