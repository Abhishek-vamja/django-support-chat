import json
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.shortcuts import get_object_or_404

from . import models
from .services.assignment import assign_conversation


@csrf_exempt
def create_session(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    data = json.loads(request.body.decode('utf-8'))
    name = data.get('name')
    email = data.get('email')
    mobile = data.get('mobile')
    ip = request.META.get('REMOTE_ADDR')
    ua = request.META.get('HTTP_USER_AGENT', '')
    visitor = models.Visitor.objects.create(name=name, email=email, mobile=mobile, ip_address=ip, user_agent=ua)
    conv = models.Conversation.objects.create(visitor=visitor, status=models.Conversation.STATUS_WAITING)

    # Broadcast to support queue
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)('support_queue', {
        'type': 'new_conversation',
        'conversation_id': str(conv.id),
        'visitor_name': visitor.name,
        'visitor_email': visitor.email,
    })

    return JsonResponse({'conversation_id': str(conv.id)})


@csrf_exempt
def send_message(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    data = json.loads(request.body.decode('utf-8'))
    conv_id = data.get('conversation_id')
    sender_type = data.get('sender_type')
    sender_id = data.get('sender_id')
    message = data.get('message')
    conv = get_object_or_404(models.Conversation, id=conv_id)
    m = models.Message.objects.create(conversation=conv, sender_type=sender_type, sender_id=sender_id, message=message)

    # Broadcast to conversation group
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(f'visitor_{conv_id}', {
        'type': 'chat.message',
        'message': {
            'id': str(m.id),
            'conversation': str(conv.id),
            'sender_type': m.sender_type,
            'sender_id': str(m.sender_id) if m.sender_id else None,
            'message': m.message,
            'created_at': m.created_at.isoformat(),
        }
    })
    return JsonResponse({'ok': True})


@csrf_exempt
def leave_conversation(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    data = json.loads(request.body.decode('utf-8'))
    conv_id = data.get('conversation_id')
    conv = get_object_or_404(models.Conversation, id=conv_id)
    conv.status = models.Conversation.STATUS_CLOSED
    conv.ended_at = timezone.now()
    conv.save()
    return JsonResponse({'ok': True})


@csrf_exempt
def submit_feedback(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    data = json.loads(request.body.decode('utf-8'))
    conv_id = data.get('conversation_id')
    agent_rating = data.get('agent_rating', 5)
    system_rating = data.get('system_rating', 5)
    comment = data.get('comment', '')
    conv = get_object_or_404(models.Conversation, id=conv_id)
    models.ConversationRating.objects.update_or_create(
        conversation=conv,
        defaults={'agent_rating': agent_rating, 'system_rating': system_rating, 'comment': comment},
    )
    return JsonResponse({'ok': True})


@csrf_exempt
def accept_conversation(request):
    # Simple agent acceptance endpoint — expects agent_id and conversation_id
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    data = json.loads(request.body.decode('utf-8'))
    conv_id = data.get('conversation_id')
    agent_id = data.get('agent_id')
    agent = get_object_or_404(models.SupportAgent, id=agent_id)
    conv_qs = models.Conversation.objects.filter(id=conv_id, status=models.Conversation.STATUS_WAITING)
    ok = assign_conversation(conv_qs, agent)
    if not ok:
        return JsonResponse({'ok': False, 'reason': 'already_assigned_or_closed'})

    # Notify agent group and visitor group
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(f'agent_{agent_id}', {
        'type': 'agent_assigned',
        'conversation_id': conv_id,
        'agent_name': agent.name,
    })
    async_to_sync(channel_layer.group_send)(f'visitor_{conv_id}', {
        'type': 'chat.message',
        'message': {
            'id': str(uuid.uuid4()),
            'conversation': conv_id,
            'sender_type': 'system',
            'sender_id': None,
            'message': f'Agent {agent.name} has joined the chat.',
            'created_at': timezone.now().isoformat(),
        }
    })

    return JsonResponse({'ok': True})
