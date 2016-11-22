from django import template
__author__ = 'clem'

register = template.Library()


@register.simple_tag
def fullname(user):
	return "%s %s" % (user.first_name, user.last_name)\

