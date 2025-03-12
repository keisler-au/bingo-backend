import json
import logging
from datetime import datetime

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from dateutil import parser
from django.forms.models import model_to_dict

from game.models import Player, Task

logger = logging.getLogger("game")


class TaskUpdatesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "task_updates"
        self.game_id = self.scope["url_route"]["kwargs"]["game_id"]
        self.group_name = f"game_{self.game_id}_updates"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        # TODO: TESTING
        # 1. Unit test
        # 2. User is shown modal and Log is sent to Sentry
        await self.send(text_data=json.dumps({"message": "WebSocket connected!"}))

    async def disconnect(self, close_code):
        # TODO: TESTING
        # 1. Unit test
        # 2. Check Redis server logs
        # - Disconnects happen automatically (offline, idle timeouts) and if user was already removed nothing happens on trying re-remove
        # - Otherwise connection issues are a bigger problem and are addressed above
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
        # TODO: TESTING
        # 1. Unit test
        # 2. This will raise an error - Check Django or Redis logs
        # - it is possible to implement a retry, but at this stage not necessary
        await self.channel_layer.group_send(
            self.group_name, {"type": "task_update", "task": task}
        )

    async def task_update(self, event):
        await self.send(text_data=json.dumps({"task": event["task"]}))

    @database_sync_to_async
    def update_task(self, task_id, player_id, last_updated):
        # TODO: TESTING
        # 1. Unit testing
        # 2. {} gets sent and frontend validation rejects processing it
        try:
            task = Task.objects.get(id=task_id)
            # TODO: TESTING
            # 1. User Pathway - Live, Unit test
            # 2. If it works it works, otherwise it errors
            last_updated = parser.parse(last_updated)
            if task.completed and last_updated < task.last_updated:
                player = Player.objects.get(id=player_id)
                task.completed_by = player
                task.last_updated = last_updated
                task.save()

            if not task.completed:
                task.completed = True
                player = Player.objects.get(id=player_id)
                task.completed_by = player
                task.last_updated = last_updated
                task.save()

            # TODO: TESTING
            # 1. Unit test
            # 2. Task and Player model needs to be here so allow thrown TypeError - check Dj logs
            task_dict = model_to_dict(task)
            task_dict["completed_by"] = model_to_dict(player)
        except Exception as e:
            logger.exception(
                "Unknown exception during Task database update", exc_info=e
            )
            task_dict = {}

        return task_dict
