import uuid
import random
import string
from django.db import models
from django.utils import timezone
from datetime import timedelta


class Visitor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField(db_index=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} <{self.email}>"


class SupportAgent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_online = models.BooleanField(default=False)
    max_concurrent_chats = models.PositiveIntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Conversation(models.Model):
    STATUS_WAITING = 'waiting'
    STATUS_ASSIGNED = 'assigned'
    STATUS_ACTIVE = 'active'
    STATUS_CLOSED = 'closed'
    STATUS_ABANDONED = 'abandoned'

    STATUS_CHOICES = (
        (STATUS_WAITING, 'Waiting'),
        (STATUS_ASSIGNED, 'Assigned'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_CLOSED, 'Closed'),
        (STATUS_ABANDONED, 'Abandoned'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name='conversations')
    assigned_agent = models.ForeignKey(
        SupportAgent, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_WAITING)
    assigned_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)

    def __str__(self):
        return f"Conversation {self.id} ({self.status})"


class Message(models.Model):
    SENDER_VISITOR = 'visitor'
    SENDER_AGENT = 'agent'
    SENDER_SYSTEM = 'system'

    SENDER_TYPE = (
        (SENDER_VISITOR, 'Visitor'),
        (SENDER_AGENT, 'Agent'),
        (SENDER_SYSTEM, 'System'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender_type = models.CharField(max_length=10, choices=SENDER_TYPE)
    sender_id = models.UUIDField(null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender_type}: {self.message[:50]}"


class ConversationRating(models.Model):
    conversation = models.OneToOneField(Conversation, on_delete=models.CASCADE, related_name='rating_obj')
    agent_rating = models.PositiveSmallIntegerField()
    system_rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating for {self.conversation.id}: {self.agent_rating}"


class AgentOTP(models.Model):
    email = models.EmailField(db_index=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)

    def __str__(self):
        return f"OTP for {self.email}"

    @staticmethod
    def generate_otp():
        return ''.join(random.choices(string.digits, k=6))


class AgentSession(models.Model):
    agent = models.OneToOneField(SupportAgent, on_delete=models.CASCADE, related_name='session')
    session_token = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    def is_valid(self):
        return timezone.now() < self.last_activity + timedelta(hours=24)

    def __str__(self):
        return f"Session for {self.agent.name}"
