import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from django.utils import timezone

from .services import auth as auth_service
from .decorators import agent_login_required
from . import models


@csrf_exempt
@require_http_methods(["POST"])
def agent_request_otp(request):
    """Agent requests OTP to be sent to their email."""
    try:
        data = json.loads(request.body.decode('utf-8'))
        email = data.get('email', '').strip()
        if not email:
            return JsonResponse({'ok': False, 'error': 'Email required'}, status=400)
        
        ok, result = auth_service.send_otp_email(email)
        if ok:
            return JsonResponse({'ok': True, 'message': 'OTP sent to your email'})
        else:
            return JsonResponse({'ok': False, 'error': 'Failed to send OTP'}, status=500)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def agent_verify_otp(request):
    """Agent verifies OTP and creates session."""
    try:
        data = json.loads(request.body.decode('utf-8'))
        email = data.get('email', '').strip()
        otp_code = data.get('otp', '').strip()
        
        if not email or not otp_code:
            return JsonResponse({'ok': False, 'error': 'Email and OTP required'}, status=400)
        
        ok, result = auth_service.verify_otp(email, otp_code)
        if not ok:
            return JsonResponse({'ok': False, 'error': result}, status=400)
        
        agent = result
        session = auth_service.create_agent_session(agent)
        
        response = JsonResponse({'ok': True, 'message': 'Login successful'})
        response.set_cookie('agent_session_token', session.session_token, max_age=86400)
        return response
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def check_otp(request):
    """Check OTP records for debugging/verification (development only)."""
    try:
        email = request.GET.get('email', '').strip()
        if not email:
            # Return all recent OTPs if no email specified
            otps = models.AgentOTP.objects.order_by('-created_at')[:10]
            data = [
                {
                    'email': otp.email,
                    'otp': otp.otp,
                    'is_verified': otp.is_verified,
                    'attempts': otp.attempts,
                    'created_at': otp.created_at.isoformat(),
                    'is_expired': otp.is_expired(),
                }
                for otp in otps
            ]
            return JsonResponse({'ok': True, 'otps': data})
        
        # Get OTP for specific email
        otp = models.AgentOTP.objects.filter(email=email).order_by('-created_at').first()
        if not otp:
            return JsonResponse({'ok': False, 'error': f'No OTP found for {email}'}, status=404)
        
        return JsonResponse({
            'ok': True,
            'email': otp.email,
            'otp': otp.otp,
            'is_verified': otp.is_verified,
            'attempts': otp.attempts,
            'created_at': otp.created_at.isoformat(),
            'is_expired': otp.is_expired(),
        })
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@agent_login_required
@require_http_methods(["GET"])
def agent_dashboard(request):
    """Agent dashboard showing waiting and active conversations."""
    agent = request.agent
    
    # Fetch conversations assigned to this agent
    conversations = models.Conversation.objects.filter(
        assigned_agent=agent
    ).select_related('visitor').order_by('-started_at')
    
    # Separate by status
    waiting = models.Conversation.objects.filter(
        status=models.Conversation.STATUS_WAITING
    ).select_related('visitor')
    
    active = conversations.filter(status=models.Conversation.STATUS_ACTIVE)
    closed = conversations.filter(status=models.Conversation.STATUS_CLOSED)
    
    context = {
        'agent': agent,
        'waiting_conversations': waiting,
        'active_conversations': active,
        'closed_conversations': closed,
    }
    return render(request, 'support_chat/agent_dashboard.html', context)


@agent_login_required
@require_http_methods(["GET"])
def agent_sidebar(request):
    """Return just the sidebar HTML for real-time updates."""
    agent = request.agent
    
    waiting = models.Conversation.objects.filter(
        status=models.Conversation.STATUS_WAITING
    ).select_related('visitor')
    
    conversations = models.Conversation.objects.filter(
        assigned_agent=agent
    ).select_related('visitor').order_by('-started_at')
    
    active = conversations.filter(status=models.Conversation.STATUS_ACTIVE)
    closed = conversations.filter(status=models.Conversation.STATUS_CLOSED)
    
    context = {
        'waiting_conversations': waiting,
        'active_conversations': active,
        'closed_conversations': closed,
    }
    return render(request, 'support_chat/sidebar.html', context)


@agent_login_required
@require_http_methods(["GET"])
def agent_chat(request, conversation_id):
    """Agent chat panel for a specific conversation."""
    agent = request.agent
    
    try:
        conversation = models.Conversation.objects.get(id=conversation_id)
    except models.Conversation.DoesNotExist:
        return render(request, 'support_chat/error.html', {'error': 'Conversation not found'}, status=404)
    
    # Check if agent is assigned
    if conversation.assigned_agent != agent:
        return render(request, 'support_chat/error.html', {'error': 'Not authorized'}, status=403)
    
    messages = conversation.messages.all()
    
    context = {
        'agent': agent,
        'conversation': conversation,
        'messages': messages,
        'visitor': conversation.visitor,
    }
    return render(request, 'support_chat/agent_chat.html', context)


@agent_login_required
@csrf_exempt
@require_http_methods(["POST"])
def agent_accept_conversation(request):
    """Agent accepts a waiting conversation."""
    agent = request.agent
    try:
        data = json.loads(request.body.decode('utf-8'))
        conv_id = data.get('conversation_id')
        
        conv_qs = models.Conversation.objects.filter(
            id=conv_id,
            status=models.Conversation.STATUS_WAITING
        )
        
        from .services.assignment import assign_conversation
        ok = assign_conversation(conv_qs, agent)
        
        if ok:
            # Broadcast to all agents that this conversation was accepted
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)('support_queue', {
                'type': 'conversation.accepted',
                'conversation_id': conv_id,
                'agent_id': str(agent.id),
                'agent_name': agent.name,
            })
            
            return JsonResponse({'ok': True, 'message': 'Conversation accepted'})
        else:
            return JsonResponse({'ok': False, 'error': 'Already assigned or closed'}, status=400)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@agent_login_required
@csrf_exempt
@require_http_methods(["POST"])
def agent_send_message(request):
    """Agent sends a message in a conversation."""
    agent = request.agent
    try:
        data = json.loads(request.body.decode('utf-8'))
        conv_id = data.get('conversation_id')
        message_text = data.get('message', '').strip()
        
        conversation = models.Conversation.objects.get(id=conv_id)
        if conversation.assigned_agent != agent:
            return JsonResponse({'ok': False, 'error': 'Not authorized'}, status=403)
        
        # Create message
        m = models.Message.objects.create(
            conversation=conversation,
            sender_type='agent',
            sender_id=agent.id,
            message=message_text
        )
        
        # Broadcast via Channels
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(f'visitor_{conv_id}', {
            'type': 'chat.message',
            'message': {
                'id': str(m.id),
                'conversation': str(conv_id),
                'sender_type': 'agent',
                'sender_id': str(agent.id),
                'message': m.message,
                'created_at': m.created_at.isoformat(),
            }
        })
        
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@agent_login_required
@csrf_exempt
@require_http_methods(["POST"])
def agent_close_conversation(request):
    """Allow agent to close a conversation and submit rating/feedback.

    Expected JSON body: {
        "conversation_id": "<uuid>",
        "agent_rating": 4,          # 1-5
        "system_rating": 5,         # optional
        "feedback": "optional text"
    }
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        conv_id = data.get('conversation_id')
        if not conv_id:
            return JsonResponse({'ok': False, 'error': 'conversation_id required'}, status=400)

        conv = get_object_or_404(models.Conversation, id=conv_id)

        # Only assigned agent may close (security)
        agent = request.agent
        if conv.assigned_agent_id != agent.id:
            return JsonResponse({'ok': False, 'error': 'Not authorized to close this conversation'}, status=403)

        # Read rating and feedback
        try:
            agent_rating = int(data.get('agent_rating', 5))
        except Exception:
            agent_rating = 5
        try:
            system_rating = int(data.get('system_rating', 5))
        except Exception:
            system_rating = 5
        feedback = data.get('feedback', '')

        # Mark conversation closed
        conv.status = models.Conversation.STATUS_CLOSED
        conv.ended_at = timezone.now()
        conv.save()

        # Save rating
        models.ConversationRating.objects.update_or_create(
            conversation=conv,
            defaults={'agent_rating': agent_rating, 'system_rating': system_rating, 'comment': feedback}
        )

        # Broadcast closure to visitor group
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(f'visitor_{conv_id}', {
            'type': 'conversation.closed',
            'conversation_id': conv_id,
        })

        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


def agent_login(request):
    """Agent login page."""
    if request.COOKIES.get('agent_session_token'):
        # Already logged in
        return redirect('support_chat:agent_dashboard')
    return render(request, 'support_chat/agent_login.html')


@agent_login_required
def agent_logout(request):
    """Agent logout."""
    token = request.COOKIES.get('agent_session_token')
    if token:
        auth_service.logout_agent(token)
    response = redirect('support_chat:agent_login')
    response.delete_cookie('agent_session_token')
    return response


@agent_login_required
@require_http_methods(["GET"])
def agent_conversations_api(request):
    """API endpoint to return all conversations for the agent as JSON."""
    agent = request.agent
    
    # Waiting conversations - visible to ALL agents (not yet assigned)
    waiting = models.Conversation.objects.filter(
        status=models.Conversation.STATUS_WAITING
    ).select_related('visitor').values('id', 'visitor__name', 'visitor__email', 'status', 'started_at')
    
    # Conversations assigned to this specific agent (both assigned and active statuses)
    my_conversations = models.Conversation.objects.filter(
        assigned_agent=agent
    ).select_related('visitor').order_by('-started_at')
    
    # Active conversations assigned to me (includes both "assigned" and "active" statuses for ongoing chats)
    active = my_conversations.filter(
        status__in=[models.Conversation.STATUS_ASSIGNED, models.Conversation.STATUS_ACTIVE]
    ).values('id', 'visitor__name', 'visitor__email', 'status', 'started_at')
    
    # Closed conversations assigned to me
    closed = my_conversations.filter(status=models.Conversation.STATUS_CLOSED).values(
        'id', 'visitor__name', 'visitor__email', 'status', 'started_at'
    )
    
    data = {
        'waiting': [
            {
                'id': str(c['id']),
                'visitor_name': c['visitor__name'],
                'visitor_email': c['visitor__email'],
                'status': c['status'],
            }
            for c in waiting
        ],
        'active': [
            {
                'id': str(c['id']),
                'visitor_name': c['visitor__name'],
                'visitor_email': c['visitor__email'],
                'status': c['status'],
            }
            for c in active
        ],
        'closed': [
            {
                'id': str(c['id']),
                'visitor_name': c['visitor__name'],
                'visitor_email': c['visitor__email'],
                'status': c['status'],
            }
            for c in closed
        ],
    }
    return JsonResponse(data)