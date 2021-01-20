from django import template
from django.utils.html import mark_safe
from core.lib import draft_to_html as draft_to_html_processor
from core.lib import hex_color_tint as hex_color_tint_processor

register = template.Library()

@register.simple_tag(name="draft_to_html", )
def draft_to_html(draft):
    return mark_safe(draft_to_html_processor(draft))

@register.simple_tag(name="hex_color_tint", )
def hex_color_tint(color, tint = 0.5):
    return hex_color_tint_processor(color, tint)