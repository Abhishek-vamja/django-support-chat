from django.urls import re_path
from . import consumers

# WebSocket URL patterns - Channels passes path WITHOUT leading slash
websocket_urlpatterns = [
    re_path(r'^ws/support/queue/?$', consumers.QueueConsumer.as_asgi()),
    re_path(r'^ws/support/agent/(?P<agent_id>[^/]+)/?$', consumers.AgentConsumer.as_asgi()),
    re_path(r'^ws/support/conversation/(?P<conversation_id>[^/]+)/?$', consumers.ConversationConsumer.as_asgi()),
]
