from django import template

register = template.Library()

@register.inclusion_tag('support_chat/widget_include.html')
def support_chat_widget():
    """
    Renders the support chat widget.
    
    Usage in templates:
        {% load support_chat_tags %}
        {% support_chat_widget %}
    """
    return {}
