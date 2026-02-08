from django.urls import path
from . import views, agent_views

app_name = 'support_chat'

urlpatterns = [
    # Visitor API
    path('api/create_session/', views.create_session, name='create_session'),
    path('api/send_message/', views.send_message, name='send_message'),
    path('api/leave_conversation/', views.leave_conversation, name='leave_conversation'),
    path('api/submit_feedback/', views.submit_feedback, name='submit_feedback'),
    path('api/accept_conversation/', views.accept_conversation, name='accept_conversation'),
    
    # Agent authentication
    path('agent/login/', agent_views.agent_login, name='agent_login'),
    path('agent/logout/', agent_views.agent_logout, name='agent_logout'),
    path('api/agent/request-otp/', agent_views.agent_request_otp, name='agent_request_otp'),
    path('api/agent/verify-otp/', agent_views.agent_verify_otp, name='agent_verify_otp'),
    path('api/agent/check-otp/', agent_views.check_otp, name='check_otp'),
    
    # Agent dashboard
    path('agent/dashboard/', agent_views.agent_dashboard, name='agent_dashboard'),
    path('agent/sidebar/', agent_views.agent_sidebar, name='agent_sidebar'),
    path('api/agent/conversations/', agent_views.agent_conversations_api, name='agent_conversations_api'),
    path('agent/chat/<uuid:conversation_id>/', agent_views.agent_chat, name='agent_chat'),
    path('api/agent/accept-conversation/', agent_views.agent_accept_conversation, name='agent_accept_conversation'),
    path('api/agent/send-message/', agent_views.agent_send_message, name='agent_send_message'),
    path('api/agent/close-conversation/', agent_views.agent_close_conversation, name='agent_close_conversation'),
]
