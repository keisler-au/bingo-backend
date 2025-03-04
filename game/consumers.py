from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import Task
from channels.db import database_sync_to_async

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
        # Receive data from WebSocket
        data = json.loads(text_data)
        task_id = data.get("task_id", None)
        action = data.get("action", None)
        title = data.get("title", "")
        description = data.get("description", "")
        completed = data.get("completed", False)

        if action == "create":
            # Create a new task and save it to the database
            task = await self.create_task(title, description, completed)
            message = f"Task '{task.title}' created."

        elif action == "update" and task_id:
            # Update an existing task in the database
            task = await self.update_task(task_id, title, description, completed)
            message = f"Task '{task.title}' updated."

        # Send the task update to all connected clients in the group
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "task_update",  # This is a custom message type
                "message": message,
                "task": {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed
                }
            }
        )

    async def task_update(self, event):
        # Send task update to the WebSocket client
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "task": event["task"]
        }))

    # Database interactions must be done in sync
    @database_sync_to_async
    def create_task(self, title, description, completed):
        task = Task.objects.create(title=title, description=description, completed=completed)
        return task

    @database_sync_to_async
    def update_task(self, task_id, title, description, completed):
        task = Task.objects.get(id=task_id)
        task.title = title
        task.description = description
        task.completed = completed
        task.save()
        return task
