from django.contrib import admin
from . import models


@admin.register(models.Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'mobile', 'created_at')
    search_fields = ('name', 'email')


@admin.register(models.SupportAgent)
class SupportAgentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'is_active', 'is_online')
    list_filter = ('is_active', 'is_online')


@admin.register(models.Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'visitor', 'assigned_agent', 'status', 'started_at', 'ended_at')
    list_filter = ('status',)
    search_fields = ('visitor__name', 'visitor__email')


@admin.register(models.Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender_type', 'created_at')
    list_filter = ('sender_type',)


@admin.register(models.ConversationRating)
class ConversationRatingAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'agent_rating', 'system_rating', 'submitted_at')


@admin.register(models.AgentOTP)
class AgentOTPAdmin(admin.ModelAdmin):
    list_display = ('email', 'otp', 'is_verified', 'attempts', 'created_at', 'is_expired_status')
    search_fields = ('email',)
    list_filter = ('is_verified', 'created_at')
    readonly_fields = ('otp', 'email', 'created_at', 'is_expired_status')
    
    def is_expired_status(self, obj):
        return "✓ Expired" if obj.is_expired() else "✗ Valid"
    is_expired_status.short_description = "Status"


@admin.register(models.AgentSession)
class AgentSessionAdmin(admin.ModelAdmin):
    list_display = ('agent', 'created_at', 'last_activity', 'is_valid_status')
    list_filter = ('created_at',)
    readonly_fields = ('agent', 'session_token', 'created_at', 'last_activity')
    
    def is_valid_status(self, obj):
        return "✓ Valid" if obj.is_valid() else "✗ Expired"
    is_valid_status.short_description = "Session Status"
