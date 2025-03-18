from django.urls import path

from game.consumers import TaskUpdatesConsumer

websocket_urlpatterns = [
    path("game_updates/<str:game_id>/<str:player_id>/", TaskUpdatesConsumer.as_asgi()),
]
