from django.db import transaction
from django.utils import timezone


def assign_conversation(conversation_qs, agent):
    """Attempt to atomically assign a waiting conversation to an agent.

    conversation_qs: a queryset filtered to the specific conversation id and status waiting
    agent: SupportAgent instance

    Returns True if assignment succeeded (row updated), False otherwise.
    """
    updated = conversation_qs.update(
        status='assigned', assigned_agent=agent, assigned_at=timezone.now()
    )
    return updated == 1
