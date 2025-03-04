import json
from datetime import datetime
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.forms.models import model_to_dict
from game.models import Task



class TaskUpdatesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Define a group name (e.g., for all users)
        self.group_name = "task_updates"  # This could be dynamic based on the task or user

        # Add the WebSocket connection to the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # Accept the WebSocket connection
        await self.accept()

        # Send a welcome message (optional)
        await self.send(text_data=json.dumps({"message": "WebSocket connected!"}))

    async def disconnect(self, close_code):
        # Remove the WebSocket connection from the group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        print("This was recieved")
        data = json.loads(text_data)
        task_id = data.get("task_id", None)
        completed = data.get("completed", False)
        completed_by = data.get("completed_by", None)
        last_updated = data.get("last_updated", datetime.now())

        task = await self.update_task(task_id, completed, completed_by, last_updated)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "task_update",
                "task": model_to_dict(task)
            }
        )

    async def task_update(self, event):
        await self.send(text_data=json.dumps({"task": event["task"]}))

    @database_sync_to_async
    def update_task(self, task_id, completed, completed_by, last_updated):
        task = Task.objects.get(id=task_id)
        task.completed = completed
        task.completed = completed_by
        task.last_updated = last_updated
        task.save()
        return task
