import secrets
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from .. import models


def send_otp_email(email):
    """Generate, save, and send OTP to agent email."""
    # Create or get latest OTP record
    otp_record = models.AgentOTP.objects.create(
        email=email,
        otp=models.AgentOTP.generate_otp()
    )
    
    subject = "Your Support Team Login OTP"
    message = f"""
Hello,

Your login OTP is: {otp_record.otp}

This code will expire in 10 minutes.

If you did not request this, please ignore this email.

Support Team
"""
    
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
        return True, otp_record
    except Exception as e:
        print(f"Email send error: {e}")
        otp_record.delete()
        return False, None


def verify_otp(email, otp_code):
    """Verify OTP and return agent if valid."""
    # Find the latest non-expired OTP for this email
    otp_record = models.AgentOTP.objects.filter(email=email).order_by('-created_at').first()
    
    if not otp_record:
        return False, "No OTP found for this email"
    
    if otp_record.is_expired():
        return False, "OTP has expired"
    
    if otp_record.attempts >= 3:
        return False, "Too many attempts. Request a new OTP."
    
    if otp_record.otp != otp_code:
        otp_record.attempts += 1
        otp_record.save()
        return False, "Invalid OTP code"
    
    # OTP is valid, get or create agent
    agent, created = models.SupportAgent.objects.get_or_create(
        email=email,
        defaults={'name': email.split('@')[0]}
    )
    
    otp_record.is_verified = True
    otp_record.save()
    
    return True, agent


def create_agent_session(agent):
    """Create a session token for the agent."""
    token = secrets.token_urlsafe(64)
    session, created = models.AgentSession.objects.get_or_create(
        agent=agent,
        defaults={'session_token': token}
    )
    if not created:
        session.session_token = token
        session.last_activity = timezone.now()
        session.save()
    return session


def get_agent_from_session(session_token):
    """Retrieve agent from valid session token."""
    try:
        session = models.AgentSession.objects.select_related('agent').get(session_token=session_token)
        if session.is_valid():
            session.last_activity = timezone.now()
            session.save()
            return session.agent
    except models.AgentSession.DoesNotExist:
        pass
    return None


def logout_agent(session_token):
    """Delete agent session."""
    models.AgentSession.objects.filter(session_token=session_token).delete()
