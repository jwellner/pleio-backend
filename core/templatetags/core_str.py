from django import template

register = template.Library()


@register.simple_tag(name='concat')
def do_concat(*parts):
    return ''.join(map(str,parts))
