from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.utils.functional import SimpleLazyObject
from django.conf import settings


def site(request):
	a_site = SimpleLazyObject(lambda: get_current_site(request))
	protocol = 'https' if request.is_secure() else 'http'
	
	return {
		'site'     : a_site,
		'site_root': SimpleLazyObject(lambda: "{0}://{1}".format(protocol, a_site.domain)),
		'site_title': settings.BREEZE_TITLE
	}


def user_context(request):
    is_auth = request.user.is_authenticated()
    is_admin = False
    # assert isinstance(request.user, User)
    is_admin = is_auth and (request.user.is_staff or request.user.is_superuser)

    return {
        'is_local_admin': is_admin,
        'is_authenticated': is_auth
    }


def date_context(_):
    import datetime
    return { 'now': datetime.datetime.now() }
