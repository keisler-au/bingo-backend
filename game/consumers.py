import asyncio
import json
import logging
import os

import redis.asyncio as redis
import sentry_sdk
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from dateutil import parser
from django.forms.models import model_to_dict

from game.models import Player, Task

logger = logging.getLogger("game")

r = redis.StrictRedis(
    host=os.getenv("REDIS_HOST"),
    port=os.getenv("REDIS_PORT"),
    password=os.getenv("REDIS_PASSWORD"),
    ssl=True,
    decode_responses=True,
)


class TaskUpdatesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope["url_route"]["kwargs"]["game_id"]
        self.player_id = self.scope["url_route"]["kwargs"]["player_id"]
        self.group_name = f"game_{self.game_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        asyncio.create_task(self.send_queued_messages())

    async def disconnect(self, close_code):
        asyncio.create_task(self.add_player_to_queue())
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        if text_data == "heartbeat":
            await self.send(text_data=json.dumps({"message": "thump"}))
            return

        data = json.loads(text_data)
        task_id = data.get("id")
        player_id = data.get("completed_by").get("id")
        last_updated = data.get("last_updated")
        task = await self.update_task(task_id, player_id, last_updated)

        if task:
            asyncio.create_task(self.enqueue_message(task))
            await self.channel_layer.group_send(
                self.group_name, {"type": "send_task_update", "task": task}
            )

    async def send_task_update(self, event):
        await self.send(text_data=json.dumps({"task": event["task"]}))

    @database_sync_to_async
    def update_task(self, task_id, player_id, last_updated):
        task_dict = {}
        try:
            task = Task.objects.get(id=task_id)
            last_updated = parser.parse(last_updated)
            if (
                task.completed
                and last_updated < task.last_updated
                or not task.completed
            ):
                player = Player.objects.get(id=player_id)
                task.completed_by = player
                task.last_updated = last_updated
                if not task.completed:
                    task.completed = True
                task.save()
                task_dict = model_to_dict(task)
                task_dict["completed_by"] = model_to_dict(player)
        except Exception as e:
            logger.exception(
                "Unknown exception during Task database update", exc_info=e
            )
            sentry_sdk.capture_exception(e)
            task_dict = None

        return task_dict

    async def add_player_to_queue(self):
        try:
            await r.rpush(f"{self.group_name}_queue", self.player_id)
            await r.expire(f"{self.group_name}_queue", 86400)
            logger.info(
                f"add_player_to_queue(), Key: {self.group_name}, Queue: {r.lrange(self.group_name, 0, -1)}"
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception("Failed redis queue update on disconnection", exc_info=e)

    async def enqueue_message(self, task):
        """Enqueue message to all offline (disconnected) players"""
        try:
            queue_name = f"{self.group_name}_queue"
            offline_player_ids = await r.lrange(queue_name, 0, -1)
            for id in offline_player_ids:
                await r.rpush(f"{self.group_name}_player_{id}", json.dumps(task))
            logger.info(
                f"enqueue_message(), Key: {queue_name}, Queue: {r.lrange(queue_name, 0, -1)}"
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception("Failed redis enqueue from recieved message", exc_info=e)

    async def send_queued_messages(self):
        """Check if there are any messages in the queue for the user when they reconnect"""
        try:
            game_queue = f"{self.group_name}_queue"
            player_queue = f"{self.group_name}_player_{self.player_id}"
            logger.info(
                f"send_queued_message(), Key: {player_queue}, Queue Before Loop: {r.lrange(player_queue, 0, -1)}"
            )
            message = True
            while message:
                message = await r.lpop(player_queue)
                logger.info(f"Message is: {message}")
                if message:
                    await self.send_task_update({"task": json.loads(message)})
            logger.info(
                f"send_queued_message(), Key: {player_queue}, Queue After Loop: {r.lrange(player_queue, 0, -1)}"
            )
            await r.lrem(game_queue, 1, self.player_id)
            logger.info(
                f"send_queued_message(), Key: {game_queue}, Queue: {r.lrange(game_queue, 0, -1)}"
            )

        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(
                "Failed to send redis queue messages on connection", exc_info=e
            )
