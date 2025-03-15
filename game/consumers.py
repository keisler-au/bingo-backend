import json
import logging
import os
from datetime import datetime

import redis
import sentry_sdk
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from dateutil import parser
from django.forms.models import model_to_dict

from game.models import Player, Task

logger = logging.getLogger("game")

r = redis.StrictRedis(
    host=os.getenv("REDIS_HOST"),
    port=os.getenv("REDIS_PORT"),
    db=0,
    decode_responses=True,
)


# TODO: UNIT TEST
class TaskUpdatesConsumer(AsyncWebsocketConsumer):
    # TODO: TESTING
    # 2. User is shown modal and Log is sent to Sentry
    async def connect(self):
        self.game_id = self.scope["url_route"]["kwargs"]["game_id"]
        self.player_id = self.scope["url_route"]["kwargs"]["player_id"]
        self.group_name = f"game_{self.game_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.send_queued_messages()

    async def disconnect(self, close_code):
        # TODO: TESTING
        # 1. Unit test
        # 2. Check Redis server logs
        # - Disconnects happen automatically (offline, idle timeouts) and if user was already removed nothing happens on trying re-remove. User channel is also removed for disconnected users with this AsyncWebsocketConsumer class
        # - Otherwise connection issues are a bigger problem and are addressed above

        r.rpush(f"{self.group_name}_queue", self.player_id)
        r.expire(f"{self.group_name}_queue", 86400)

        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        # TODO: TESTING
        # 1. Unit test
        # 2. It will only error during edge cases, most likely server issues - Check Django logs
        if text_data == "heartbeat":
            await self.send(text_data=json.dumps({"message": "thump"}))
            return
        # TODO: TESTING
        # 1. Unit test - negative pathway
        # 2. Will raise a JSONDecodeError - Check Django logs
        data = json.loads(text_data)
        # TODO: TESTING
        # 1. Unit test
        # 2. Will raise an AttributeError - Check Django logs
        task_id = data.get("id")
        player_id = data.get("completed_by").get("id")
        last_updated = data.get("last_updated")
        task = await self.update_task(task_id, player_id, last_updated)
        if task:
            self.enqueue_message(task)
            # TODO: TESTING
            # 1. Unit test
            # 2. This will raise an error - Check Django or Redis logs
            # - it is possible to implement a retry, but at this stage not necessary
            await self.channel_layer.group_send(
                self.group_name, {"type": "task_update", "task": task}
            )

    async def task_update(self, event):
        await self.send(text_data=json.dumps({"task": event["task"]}))

    # SHOULD THIS BE DATABASE ASYNC
    # @database_sync_to_async
    async def send_queued_messages(self):
        """Check if there are any messages in the queue for the user when they reconnect"""
        self.queue_name = f"{self.group_name}_player_{self.player_id}"

        message = True
        while message:
            message = r.lpop(self.queue_name)
            if message:
                await self.task_update({"task": json.loads(message)})
        r.lrem(f"{self.game_name}_queue", 1, self.player_id)

    async def enqueue_message(self, task):
        """Enqueue message to all offline (disconnected) players"""
        # get list of player queue keys
        # push to each queue
        offline_player_ids = r.lrange(f"{self.group_name}_queue", 0, -1)
        for id in offline_player_ids:
            r.rpush(f"{self.group_name}_player_{id}", json.dumps(task))

    @database_sync_to_async
    def update_task(self, task_id, player_id, last_updated):
        # TODO: TESTING
        # 1. Unit testing
        # 2. {} gets sent and frontend validation rejects processing it
        task_dict = {}
        try:
            task = Task.objects.get(id=task_id)
            # TODO: TESTING
            # 1. User Pathway - Live, Unit test
            # 2. If it works it works, otherwise it errors
            last_updated = parser.parse(last_updated)
            # TODO: TESTING
            # 1. Unit test
            # 2. Task and Player model needs to be here so allow thrown TypeError - check Dj logs
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
