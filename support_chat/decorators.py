from functools import wraps
from django.shortcuts import redirect
from .services.auth import get_agent_from_session


def agent_login_required(view_func):
    """Decorator to require agent authentication via session cookie."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        token = request.COOKIES.get('agent_session_token')
        if token:
            agent = get_agent_from_session(token)
            if agent:
                request.agent = agent
                return view_func(request, *args, **kwargs)
        return redirect('support_chat:agent_login')
    return wrapper
