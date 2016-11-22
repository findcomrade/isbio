from django import template
from django.conf import settings
__author__ = 'clem'

register = template.Library()

@register.simple_tag
def fullname(user):
	return "%s %s" % (user.first_name, user.last_name)\


@register.simple_tag
def run_mode_name():
	return 'dev' if settings.DEV_MODE else ''
