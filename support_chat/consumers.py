import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from . import models


class QueueConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('support_queue', self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard('support_queue', self.channel_name)

    async def new_conversation(self, event):
        await self.send_json(event)

    async def conversation_accepted(self, event):
        """Broadcast when a conversation is accepted by an agent."""
        await self.send_json({
            'type': 'conversation_accepted',
            'conversation_id': event['conversation_id'],
            'agent_id': event['agent_id'],
            'agent_name': event['agent_name'],
        })


class AgentConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.agent_id = self.scope['url_route']['kwargs'].get('agent_id')
        if not self.agent_id:
            return await self.close()
        await self.channel_layer.group_add(f'agent_{self.agent_id}', self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(f'agent_{self.agent_id}', self.channel_name)

    async def agent_assigned(self, event):
        await self.send_json(event)


class ConversationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs'].get('conversation_id')
        if not self.conversation_id:
            return await self.close()
        
        # Subscribe both visitor and agent groups
        self.visitor_group = f'visitor_{self.conversation_id}'
        self.agent_group = f'agent_conversation_{self.conversation_id}'
        
        await self.channel_layer.group_add(self.visitor_group, self.channel_name)
        await self.channel_layer.group_add(self.agent_group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.visitor_group, self.channel_name)
        await self.channel_layer.group_discard(self.agent_group, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # Expect messages: {"type": "message", "sender_type": "visitor|agent", "message": "...", "sender_id": "uuid"}
        if content.get('type') == 'message':
            await self.handle_message(content)
        elif content.get('type') == 'close_conversation':
            await self.handle_close_conversation(content)

    @database_sync_to_async
    def save_message(self, conversation_id, sender_type, sender_id, message_text):
        conv = models.Conversation.objects.get(id=conversation_id)
        m = models.Message.objects.create(
            conversation=conv,
            sender_type=sender_type,
            sender_id=sender_id,
            message=message_text,
        )
        return {
            'id': str(m.id),
            'conversation': str(conv.id),
            'sender_type': m.sender_type,
            'sender_id': str(m.sender_id) if m.sender_id else None,
            'message': m.message,
            'created_at': m.created_at.isoformat(),
        }

    @database_sync_to_async
    def close_conversation(self, conversation_id):
        """Close conversation (only visitors can close)."""
        conv = models.Conversation.objects.get(id=conversation_id)
        conv.status = models.Conversation.STATUS_CLOSED
        conv.ended_at = timezone.now()
        conv.save()
        return str(conv.id)

    async def handle_message(self, content):
        saved = await self.save_message(
            self.conversation_id,
            content.get('sender_type'),
            content.get('sender_id'),
            content.get('message'),
        )
        # Broadcast to both groups (visitor and agent)
        await self.channel_layer.group_send(
            self.visitor_group,
            {
                'type': 'chat.message',
                'message': saved,
            },
        )
        await self.channel_layer.group_send(
            self.agent_group,
            {
                'type': 'chat.message',
                'message': saved,
            },
        )

    async def handle_close_conversation(self, content):
        """Handle conversation closure from visitor side only."""
        await self.close_conversation(self.conversation_id)
        # Notify both parties that conversation is closed
        await self.channel_layer.group_send(
            self.visitor_group,
            {
                'type': 'conversation.closed',
                'conversation_id': self.conversation_id,
            },
        )
        await self.channel_layer.group_send(
            self.agent_group,
            {
                'type': 'conversation.closed',
                'conversation_id': self.conversation_id,
            },
        )

    async def chat_message(self, event):
        await self.send_json({'type': 'message', 'payload': event['message']})

    async def conversation_closed(self, event):
        await self.send_json({'type': 'conversation_closed', 'conversation_id': event['conversation_id']})

