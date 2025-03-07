import json
from datetime import datetime
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.forms.models import model_to_dict
from game.models import Task, Player



class TaskUpdatesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "task_updates" 

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        await self.send(text_data=json.dumps({"message": "WebSocket connected!"}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        task_id = data.get("id", None)
        completed = data.get("completed", False)
        player_id = data.get("completed_by", "{}").get("id")
        last_updated = data.get("last_updated", datetime.now())
        task = await self.update_task(task_id, completed, player_id, last_updated)
        print("WHAT ABOUT THIS = ", task)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "task_update",
                "task": task
            }
        )

    async def task_update(self, event):
        await self.send(text_data=json.dumps({"task": event["task"]}))

    @database_sync_to_async
    def update_task(self, task_id, completed, player_id, last_updated):
        task = Task.objects.get(id=task_id)
        player = Player.objects.get(id=player_id)
        task.completed = completed
        task.completed_by = player
        task.last_updated = last_updated
        task.save()
        task_dict = model_to_dict(task)
        task_dict["completed_by"] = model_to_dict(player)
        return task_dict
