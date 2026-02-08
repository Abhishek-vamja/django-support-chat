# Django Support Chat Library - Quick Usage Summary

## What It Does
A real-time support chat widget for your Django website. Visitors click a floating button to chat with support agents in real-time.

---

## Installation (5 Steps)

### 1. Copy the Library
```
your_project/
├── manage.py
└── support_chat/  ← Copy here
```

### 2. Update `settings.py`
```python
INSTALLED_APPS = [
    'daphne',
    'channels',
    'support_chat',  # Add this
    # ... other apps
]

ASGI_APPLICATION = 'your_project.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {'hosts': [('127.0.0.1', 6379)]},
    },
}
```

### 3. Update `asgi.py`
```python
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from support_chat.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
})
```

### 4. Update `urls.py`
```python
urlpatterns = [
    path('support_chat/', include('support_chat.urls')),
]
```

### 5. Run Migrations
```bash
python manage.py migrate support_chat
```

---

## How to Use (2 Lines of Code!)

### Add to Your Base Template
```django
{% load support_chat_tags %}

<!-- Add this anywhere in your template -->
{% support_chat_widget %}
```

That's it! The widget will appear on all pages.

---

## Running the App

### Terminal 1: Start Redis
```bash
redis-server
```

### Terminal 2: Start Django (ASGI)
```bash
daphne -b 127.0.0.1 -p 8000 your_project.asgi:application
```

### Terminal 3: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

---

## Create a Support Agent

Go to: `http://localhost:8000/admin/`

**Support Chat → Support Agents → Add Agent**
- Name: "John Support"
- Email: "john@example.com"

---

## Test It

1. **As Customer:**
   - Open your website
   - Click chat button (bottom right)
   - Enter name and email
   - Send a message

2. **As Agent:**
   - Go to: `http://localhost:8000/support_chat/agent/dashboard/`
   - Login with agent email
   - Enter OTP (check email in `/sent_emails/`)
   - Click "Accept" on conversation
   - Chat with customer!

---

## Key URLs

| Page | URL |
|------|-----|
| Website | `http://localhost:8000/` |
| Admin | `http://localhost:8000/admin/` |
| Agent Dashboard | `http://localhost:8000/support_chat/agent/dashboard/` |

---

## Customize Widget Colors

Edit `support_chat/static/support_chat/css/widget.css`:

```css
.sc-fab {
    background: linear-gradient(135deg, #your-color-1 0%, #your-color-2 100%);
}
```

---

## Common Issues

| Problem | Solution |
|---------|----------|
| Widget not showing | Check `{% load support_chat_tags %}` in template |
| Messages not sending | Start Redis: `redis-server` |
| Static files missing | Run `python manage.py collectstatic` |
| OTP not received | Check `/sent_emails/` folder |

---

## Requirements

- Python 3.8+
- Django 4.0+
- Redis 5.0+
- Channels 3.0+
- Daphne 3.0+

Install with:
```bash
pip install Django==6.0.2 Channels==3.0.5 Daphne==3.0.2 channels-redis==4.1.0
```

---

## That's All!

Your support chat is now live. Visitors can chat with agents in real-time.

For detailed docs, check the `docs/` folder.
